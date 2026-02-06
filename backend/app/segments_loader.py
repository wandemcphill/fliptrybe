import pkgutil
import importlib
from flask import Blueprint

def _iter_segment_modules():
    import app.segments as segments_pkg
    for m in pkgutil.iter_modules(segments_pkg.__path__):
        if m.ispkg:
            continue
        yield f"{segments_pkg.__name__}.{m.name}"

def register_all_segment_blueprints(app):
    registered = []
    import_errors = []
    for mod_name in _iter_segment_modules():
        try:
            module = importlib.import_module(mod_name)
        except Exception as e:
            # Many segments are optional or may depend on modules that are not yet
            # implemented. Never let a single segment prevent the whole API from
            # booting, especially during integration work.
            app.logger.warning(f"Skipping segment {mod_name} due to import error: {e}")
            import_errors.append({"module": mod_name, "error": str(e)})
            continue
        for obj in module.__dict__.values():
            if isinstance(obj, Blueprint):
                if obj.name in app.blueprints:
                    continue
                app.register_blueprint(obj)
                registered.append(obj.name)
    # Optional: expose what loaded for debugging
    app.logger.info("Registered segment blueprints: %s", registered)
    app.config["SEGMENT_IMPORT_ERRORS"] = import_errors
