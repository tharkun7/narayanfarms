ValueError: This app has encountered an error. The original error message is redacted to prevent data leaks. Full error details have been recorded in the logs (if you're on Streamlit Cloud, click on 'Manage app' in the lower right of your app).
Traceback:
File "/mount/src/narayanfarms/app.py", line 118, in <module>
    batch_df = pd.DataFrame(new_entries, columns=df_entry.columns)
File "/home/adminuser/venv/lib/python3.13/site-packages/pandas/core/frame.py", line 855, in __init__
    arrays, columns, index = nested_data_to_arrays(
                             ~~~~~~~~~~~~~~~~~~~~~^
        # error: Argument 3 to "nested_data_to_arrays" has incompatible
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<4 lines>...
        dtype,
        ^^^^^^
    )
    ^
File "/home/adminuser/venv/lib/python3.13/site-packages/pandas/core/internals/construction.py", line 520, in nested_data_to_arrays
    arrays, columns = to_arrays(data, columns, dtype=dtype)
                      ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/home/adminuser/venv/lib/python3.13/site-packages/pandas/core/internals/construction.py", line 845, in to_arrays
    content, columns = _finalize_columns_and_data(arr, columns, dtype)
                       ~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
File "/home/adminuser/venv/lib/python3.13/site-packages/pandas/core/internals/construction.py", line 942, in _finalize_columns_and_data
    raise ValueError(err) from err
