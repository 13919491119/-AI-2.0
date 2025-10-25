"""Simple FastAPI inference smoke service.

Provides lightweight endpoints for health, model-info, predict and reload.
This file is intentionally minimal for smoke testing; model loading is done
asynchronously on startup to avoid blocking the server.
"""
# pyright: ignore[reportMissingImports]
from fastapi import FastAPI, HTTPException # pyright: ignore[reportMissingImports]
from pydantic import BaseModel # pyright: ignore[reportMissingImports]
import threading


app = FastAPI(title="Xuanji AI API")


# Delay model loading to avoid blocking startup
_model_lock = threading.Lock()
_model = None
_data_manager = None


class PredictRequest(BaseModel):
    input: list | None = None


def load_model():
    """Load or initialize the model (thread-safe).

    Raises RuntimeError if required modules cannot be imported.
    """
    global _model, _data_manager
    with _model_lock:
        if _model is not None:
            return _model
        try:
            from ssq_data import SSQDataManager
            from ssq_ai_model import SSQAIModel
        except Exception as e:
            raise RuntimeError(f"加载模型依赖失败: {e}")

        _data_manager = SSQDataManager()
        _data_manager.fetch_online()  # ensure some data exists
        _model = SSQAIModel(_data_manager)

        # Try a light train if necessary; ignore errors to keep service up
        try:
            _model.train()
        except Exception:
            pass

        return _model


@app.on_event("startup")
def startup_event():
    """Kick off background model loading on startup."""

    def _bg_load():
        try:
            load_model()
        except Exception as exc:
            # don't raise; just log to stdout for smoke tests
            print(f"模型异步加载警告: {exc}")

    t = threading.Thread(target=_bg_load, daemon=True)
    t.start()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/model-info")
def model_info():
    try:
        m = load_model()
        return {"trained_count": getattr(m, "cumulative_train_count", 0)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/predict")
def predict(req: PredictRequest):
    try:
        m = load_model()
        inp = req.input
        if inp is None:
            reds, blue = m.predict()
        else:
            reds, blue = m.predict(inp)
        return {"reds": reds, "blue": blue}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/reload-model")
def reload_model():
    global _model, _data_manager
    with _model_lock:
        _model = None
        _data_manager = None
    try:
        load_model()
        return {"reloaded": True}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
