import modal
import sys

app = modal.App("trl-debug")
image = modal.Image.debian_slim(python_version="3.11").pip_install("trl")

@app.function(image=image)
def find_data_collator():
    import trl
    results = []
    
    # Check top level
    results.extend([f"trl.{k}" for k in dir(trl) if 'collator' in k.lower()])
    
    # Try importing typical submodules
    try:
        import trl.trainer
        results.extend([f"trl.trainer.{k}" for k in dir(trl.trainer) if 'collator' in k.lower()])
    except ImportError:
        pass
        
    try:
        import trl.core
        results.extend([f"trl.core.{k}" for k in dir(trl.core) if 'collator' in k.lower()])
    except ImportError:
        pass

    import pkgutil
    import importlib
    for importer, modname, ispkg in pkgutil.walk_packages(path=trl.__path__, prefix=trl.__name__+'.'):
        try:
            mod = importlib.import_module(modname)
            results.extend([f"{modname}.{k}" for k in dir(mod) if 'collator' in k.lower()])
        except Exception:
            pass

    return list(set(results))

@app.local_entrypoint()
def main():
    print("Finding DataCollator locations in TRL...")
    results = find_data_collator.remote()
    for r in results:
        print(r)
