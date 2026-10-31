"""CaP-X の特権情報ありの API を包んで、現実に近い条件を足す拡張。

- *_Noisy:   物体や掴み位置の「位置」に、呼ぶたびに独立なガウス誤差を足す（画像認識の誤差の代わり）。
             標準偏差は環境変数 PAI_POSE_NOISE_M（メートル、既定 0.01）。
- *_NoGrasp: sample_grasp_pose を外す。掴む位置と向きを LLM が自分で決める必要がある。
- *_NoisyNoGrasp: 両方。

CaP-X の capx/integrations/__init__.py の最後から import され、register_api で登録される。
"""

from __future__ import annotations

import functools
import inspect
import os
from typing import Any, Callable

import numpy as np

from capx.integrations.base_api import ApiBase, get_api, register_api

# 位置を返す関数（戻り値の先頭が XYZ）
POSE_FUNCS = ("get_object_pose", "sample_grasp_pose", "get_hammer_pose")
NOISE_NOTE = (
    "\nNote: positions returned here come from a perception system and contain random errors "
    "(roughly 1 cm standard deviation, independent on every call)."
)


def _noise_sigma() -> float:
    return float(os.getenv("PAI_POSE_NOISE_M", "0.01"))


def _wrap_noisy(fn: Callable[..., Any], rng: np.random.Generator) -> Callable[..., Any]:
    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        out = fn(*args, **kwargs)
        sigma = _noise_sigma()
        if sigma <= 0:
            return out
        if isinstance(out, tuple) and len(out) >= 1:
            pos = np.asarray(out[0], dtype=np.float64).copy()
            pos[:3] = pos[:3] + rng.normal(0.0, sigma, size=3)
            return (pos, *out[1:])
        if isinstance(out, np.ndarray) and out.shape[-1] >= 3:
            arr = np.asarray(out, dtype=np.float64).copy()
            arr[..., :3] = arr[..., :3] + rng.normal(0.0, sigma, size=3)
            return arr
        return out

    wrapper.__doc__ = (inspect.getdoc(fn) or "") + NOISE_NOTE
    return wrapper


def make_variant(base_factory: Callable[[Any], ApiBase], noisy: bool, no_grasp: bool) -> Callable[[Any], ApiBase]:
    """登録済みの作り方（引数付きのものもある）で API を作り、functions() だけ差し替える。"""

    def factory(env: Any) -> ApiBase:
        api = base_factory(env)
        original = api.functions
        rng = np.random.default_rng()
        cache: dict[str, Callable[..., Any]] = {}

        def functions() -> dict[str, Callable[..., Any]]:
            # 同じ関数オブジェクトを返し続ける（プロンプトと実行で食い違わないように）
            if not cache:
                funcs = dict(original())
                if no_grasp:
                    funcs.pop("sample_grasp_pose", None)
                if noisy:
                    for name in POSE_FUNCS:
                        if name in funcs:
                            funcs[name] = _wrap_noisy(funcs[name], rng)
                cache.update(funcs)
            return cache

        api.functions = functions  # type: ignore[method-assign]
        return api

    return factory


BASES = [
    "FrankaControlPrivilegedApi",
    "FrankaControlNutAssemblyPrivilegedApi",
    "FrankaControlSpillWipePrivilegedApi",
    "FrankaHandoverPrivilegedApi",
]

for _name in BASES:
    _base_factory = get_api(_name)
    for _noisy, _no_grasp, _suffix in [
        (True, False, "Noisy"),
        (False, True, "NoGrasp"),
        (True, True, "NoisyNoGrasp"),
    ]:
        register_api(f"{_name}_{_suffix}", make_variant(_base_factory, _noisy, _no_grasp))
