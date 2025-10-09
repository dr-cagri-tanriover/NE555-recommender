
import functools

def assert_notifier(func):
    """
    Decorator: catches AssertionError inside a function and prints
    a message including the function name before re-raising the error.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AssertionError as e:
            func_name = func.__name__
            print(f"❌ Assertion failed in function '{func_name}()': {e}")
            raise  # re-raise the assertion for visibility
    return wrapper

