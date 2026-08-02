from pathlib import Path
# pyrefly: ignore [missing-import]
import joblib

MODEL_DIR = Path("app/ml/models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)


class ModelManager:

    @staticmethod
    def model_path(product_name: str):
        safe_name = (
            product_name.replace(" ", "_")
                        .replace("/", "_")
        )
        return MODEL_DIR / f"{safe_name}.pkl"

    @staticmethod
    def save(product_name: str, model, confidence: float):
        path = ModelManager.model_path(product_name)
        data = {
            "model": model,
            "confidence": confidence
        }
        joblib.dump(data, path)

    @staticmethod
    def load(product_name: str):
        path = ModelManager.model_path(product_name)

        if path.exists():
            try:
                data = joblib.load(path)
                if isinstance(data, dict) and "model" in data:
                    return data
            except Exception:
                pass

        return None