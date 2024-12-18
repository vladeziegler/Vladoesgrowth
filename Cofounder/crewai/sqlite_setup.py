import sys
import warnings

def ensure_pysqlite3():
    try:
        import pysqlite3
        # Replace sqlite3 with pysqlite3
        sys.modules['sqlite3'] = pysqlite3
    except ImportError:
        warnings.warn(
            "pysqlite3 not found. Using system sqlite3. "
            "This might cause issues if your system sqlite3 version is < 3.35.0"
        )
        return
    except Exception as e:
        warnings.warn(f"Error setting up pysqlite3: {str(e)}")
        return
        
# import sys
# import subprocess
# import importlib

# def ensure_pysqlite3():
#     try:
#         import pysqlite3
#         # Replace sqlite3 with pysqlite3
#         sys.modules['sqlite3'] = pysqlite3
#     except ImportError:
#         # If pysqlite3 is not installed, try to install it
#         subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pysqlite3-binary'])
#         import pysqlite3
#         sys.modules['sqlite3'] = pysqlite3