#!/usr/bin/env python
"""
Input/output functions to read and write Synapse tables.

Authors:
    - Arno Klein, 2015  (arno@sagebase.org)  http://binarybottle.com

Copyright 2015,  Sage Bionetworks (http://sagebase.org), Apache v2.0 License

"""


def read_synapse_table_files(synapse_table_id,
                             column_names=[], download_limit=None,
                             out_path='.', username='', password=''):
    """
    Read data from a Synapse table. If column_names specified, download files.

    Parameters
    ----------
    synapse_table_id : string
        Synapse ID for table
    column_names : list of strings
        column headers for columns with fileIDs (if wish to download files)
    download_limit : int
        limit file downloads to this number of rows (None = all rows)
    out_path : string
        output path to store column_name files
    username : string
        Synapse username (only needed once on a given machine)
    password : string
        Synapse password (only needed once on a given machine)

    Returns
    -------
    table_data : Pandas DataFrame
        Synapse table contents
    downloaded_files : list of lists of strings
        files from Synapse table column(s) (full paths to downloaded files)

    Examples
    --------
    >>> from mhealthx.synapse_io import read_synapse_table_files
    >>> synapse_table_id = 'syn4590865' #'syn4907789'
    >>> column_names = ['audio_audio.m4a', 'audio_countdown.m4a']
    >>> download_limit = 3  # None = download files from all rows
    >>> out_path = '.'
    >>> username = ''
    >>> password = ''
    >>> table_data, downloaded_files = read_synapse_table_files(synapse_table_id, column_names, download_limit, out_path, username, password)

    """
    import synapseclient
    import numpy as np

    syn = synapseclient.Synapse()

    # Log in to Synapse:
    if username and password:
        syn.login(username, password)
    else:
        syn.login()

    # Download Synapse table schema and table_data:
    schema = syn.get(synapse_table_id)
    query = "select * from {0}".format(synapse_table_id)
    results = syn.tableQuery(query)
    table_data = results.asDataFrame()
    downloaded_files = []

    # Download Synapse files for fileIDs in specified table columns:
    if column_names:

        # Set the number of rows to loop through:
        if type(download_limit) != int:
            download_limit = table_data.shape[0]

        # Loop through specified columns:
        for column_name in column_names:
            column_data = table_data[column_name]

            # Loop through specified number of rows:
            files_per_column = []
            for irow in range(download_limit):

                # If there is no file in that row, save None:
                if np.isnan(column_data[irow]):
                    files_per_column.append(None)

                # Download the file:
                else:
                    fileinfo = syn.downloadTableFile(schema,
                                                 rowId=irow,
                                                 versionNumber=0,
                                                 column=column_name,
                                                 downloadLocation=out_path)
                    if fileinfo:
                        files_per_column.append(fileinfo['path'])
                    else:
                        files_per_column.append('')

            downloaded_files.append(files_per_column)

    return table_data, downloaded_files


def copy_synapse_table(synapse_table_id, synapse_project_id, table_name='',
                       remove_columns=[], username='', password=''):
    """
    Copy Synapse table to another Synapse project.

    Parameters
    ----------
    synapse_table_id : string
        Synapse ID for table to copy
    synapse_project_id : string
        copy table to project with this Synapse ID
    table_name : string
        schema name of table
    remove_columns : list of strings
        column headers for columns to be removed
    username : string
        Synapse username (only needed once on a given machine)
    password : string
        Synapse password (only needed once on a given machine)

    Returns
    -------
    table_data : Pandas DataFrame
        Synapse table contents
    table_name : string
        schema name of table
    synapse_project_id : string
        Synapse ID for project within which table is to be written

    Examples
    --------
    >>> from mhealthx.synapse_io import copy_synapse_table
    >>> synapse_table_id = 'syn4590865'
    >>> synapse_project_id = 'syn4899451'
    >>> table_name = 'Copy of ' + synapse_table_id
    >>> remove_columns = ['audio_audio.m4a', 'audio_countdown.m4a']
    >>> username = ''
    >>> password = ''
    >>> table_data, table_name, synapse_project_id = copy_synapse_table(synapse_table_id, synapse_project_id, table_name, remove_columns, username, password)

    """
    import synapseclient
    from synapseclient import Schema
    from synapseclient.table import Table, as_table_columns

    syn = synapseclient.Synapse()

    # Log in to Synapse:
    if username and password:
        syn.login(username, password)
    else:
        syn.login()

    # Download Synapse table as a dataframe:
    results = syn.tableQuery("select * from {0}".format(synapse_table_id))
    table_data = results.asDataFrame()

    # Remove specified columns:
    if remove_columns:
        for remove_column in remove_columns:
            del table_data[remove_column]

    # Upload to Synapse table:
    table_data.index = range(table_data.shape[0])
    schema = Schema(name=table_name, columns=as_table_columns(table_data),
                    parent=synapse_project_id,
                    includeRowIdAndRowVersion=False)
    table = syn.store(Table(schema, table_data))

    return table_data, table_name, synapse_project_id


def write_synapse_table(table_data, synapse_project_id, table_name='',
                        username='', password=''):
    """
    Write data to a Synapse table.

    Parameters
    ----------
    table_data : Pandas DataFrame
        Synapse table contents
    synapse_project_id : string
        Synapse ID for project within which table is to be written
    table_name : string
        schema name of table
    username : string
        Synapse username (only needed once on a given machine)
    password : string
        Synapse password (only needed once on a given machine)

    Examples
    --------
    >>> from mhealthx.synapse_io import read_synapse_table_files, write_synapse_table
    >>> in_synapse_table_id = 'syn4590865'
    >>> synapse_project_id = 'syn4899451'
    >>> column_names = []
    >>> download_limit = None
    >>> out_path = '.'
    >>> username = ''
    >>> password = ''
    >>> table_data, files = read_synapse_table_files(in_synapse_table_id, column_names, download_limit, out_path, username, password)
    >>> table_name = 'Contents of ' + in_synapse_table_id
    >>> write_synapse_table(table_data, synapse_project_id, table_name, username, password)

    """
    import synapseclient
    from synapseclient import Schema, Table, as_table_columns

    syn = synapseclient.Synapse()

    # Log in to Synapse:
    if username and password:
        syn.login(username, password)
    else:
        syn.login()

    table_data.index = range(table_data.shape[0])

    schema = Schema(name=table_name, columns=as_table_columns(table_data),
                    parent=synapse_project_id, includeRowIdAndRowVersion=False)

    syn.store(Table(schema, table_data))


def files_to_synapse_table(in_files, synapse_project_id, table_name,
                           column_name='fileID', username='', password=''):
    """
    Upload files and file handle IDs to Synapse.

    Parameters
    ----------
    in_files : list of strings
        paths to files to upload to Synapse
    synapse_project_id : string
        Synapse ID for project to which table is to be written
    table_name : string
        schema name of table
    column_name : string
        header for column of fileIDs
    username : string
        Synapse username (only needed once on a given machine)
    password : string
        Synapse password (only needed once on a given machine)

    Returns
    -------
    synapse_project_id : string
        Synapse ID for project

    Examples
    --------
    >>> from mhealthx.synapse_io import files_to_synapse_table
    >>> in_files = ['/Users/arno/Local/wav/test1.wav']
    >>> synapse_project_id = 'syn4899451'
    >>> table_name = 'Test to store files and file handle IDs'
    >>> column_name = 'fileID1'
    >>> username = ''
    >>> password = ''
    >>> table_data, synapse_project_id = files_to_synapse_table(in_files, synapse_project_id, table_name, column_name, username, password)
    >>> #column_name = 'fileID2'
    >>> #in_files = ['/Users/arno/Local/wav/test2.wav']
    >>> #table_data, synapse_project_id = files_to_synapse_table(in_files, synapse_project_id, table_name, column_name, username, password)

    """
    import synapseclient
    from synapseclient import Schema
    from synapseclient.table import Column, RowSet, Row

    syn = synapseclient.Synapse()

    # Log in to Synapse:
    if username and password:
        syn.login(username, password)
    else:
        syn.login()

    # Store file handle IDs:
    files_handles = []
    for in_file in in_files:
        file_handle = syn._chunkedUploadFile(in_file)
        files_handles.append([file_handle['id']])

    # New column headers:
    new_column_header = Column(name=column_name, columnType='FILEHANDLEID')

    # See if Synapse table exists:
    # tex = list(syn.chunkedQuery("select id from Table where parentId=='{0}'"
    #                             " and name=='{1}'".format(synapse_project_id,
    #                                                       table_name)))
    # If Synapse table does not exist, create table schema:
    # if not tex:

    # Create table schema:
    schema = syn.store(Schema(name=table_name,
                              columns=[new_column_header],
                              parent=synapse_project_id))

    # Upload files and file handle IDs with new schema:
    syn.store(RowSet(columns=[new_column_header], schema=schema,
                     rows=[Row(r) for r in files_handles]))

    # If Synapse table exists, get table ID and update table schema:
    # else:
    #
    #     # Download Synapse table schema and table_data:
    #     schema = syn.get(synapse_table_id)
    #     results = syn.tableQuery("select * from {0}".format(synapse_table_id))
    #     table_data = results.asDataFrame()
    #
    #     synapse_table_id = tex[0]['Table.id']
    #     schema = syn.get(synapse_table_id)
    #     new_column = syn.store(new_column_header)
    #     schema.addColumn(new_column)
    #     schema = syn.store(schema)
    #
    #     # Upload files and file handle IDs with new schema:
    #     syn.store(RowSet(columns=[new_column_header], schema=schema,
    #                      rows=[Row(r) for r in files_handles]))


def concatenate_tables_to_synapse_table(tables, synapse_project_id,
                                        table_name,
                                        transpose_tables=False, start_row=0,
                                        username='', password=''):
    """
    Concatenate multiple table files or dataframes,
    increasing the number of columns, and store as a Synapse table.

    Parameters
    ----------
    tables : list of strings or pandas DataFrames
        DataFrames or paths to files
    synapse_project_id : string
        Synapse ID for project to which output is to be written
    table_name : string
        schema name of table
    transpose_tables : Boolean
        transpose tables before concatenating?
    start_row : integer
        starting row for each table before concatenating
        (use all rows for first table)
    username : string
        Synapse username (only needed once on a given machine)
    password : string
        Synapse password (only needed once on a given machine)

    Returns
    -------
    table_data : Pandas DataFrame
        output table data
    table_name : string
        schema name of table
    synapse_table_id : string
        Synapse ID for table
    synapse_project_id : string
        Synapse ID for project

    Examples
    --------
    >>> import pandas as pd
    >>> from mhealthx.synapse_io import concatenate_tables_to_synapse_table
    >>> # Example with DataFrames:
    >>> df1 = pd.DataFrame({'A': ['A0', 'A1', 'A2', 'A3'],
    >>>                     'B': ['B0', 'B1', 'B2', 'B3'],
    >>>                     'C': ['C0', 'C1', 'C2', 'C3'],
    >>>                     'D': ['D0', 'D1', 'D2', 'D3']},
    >>>                    index=[0, 1, 2, 3])
    >>> df2 = pd.DataFrame({'E': ['A4', 'A5', 'A6', 'A7'],
    >>>                     'F': ['B4', 'B5', 'B6', 'B7'],
    >>>                     'G': ['C4', 'C5', 'C6', 'C7'],
    >>>                     'H': ['D4', 'D5', 'D6', 'D7']},
    >>>                     index=[0, 1, 2, 3])
    >>> tables = [df1, df2]
    >>>
    >>> # Example with csv files:
    >>> #tables = ['/Users/arno/csv/test1.csv', '/Users/arno/csv/test2.csv']
    >>>
    >>> synapse_project_id = 'syn4899451'
    >>> table_name = 'Test to join tables'
    >>> transpose_tables = True
    >>> start_row = 0
    >>> username = ''
    >>> password = ''
    >>> table_data, table_name, synapse_table_id, synapse_project_id = concatenate_tables_to_synapse_table(tables, synapse_project_id, table_name, transpose_tables, start_row, username, password)
    """
    import pandas as pd
    import synapseclient
    from synapseclient import Schema, Table, as_table_columns

    syn = synapseclient.Synapse()

    # Log in to Synapse:
    if username and password:
        syn.login(username, password)
    else:
        syn.login()

    # Raise an error if tables are not strings or pandas DataFrames:
    if not type(tables[0]) == str and not type(tables[0]) == pd.DataFrame:
        raise IOError("'tables' should contain file path strings"
                      " or pandas DataFrames.")
    # Concatenate table files:
    elif type(tables[0]) == str:
        dfs = []
        first_table = True
        for table_file in tables:
            df = pd.read_table(table_file, index_col=False)
            if transpose_tables:
                df = df.transpose()
            if start_row > 0 and not first_table:
                if start_row > df.shape[0]:
                    raise IOError("The start_row is bigger than the table!")
                df = df[start_row:df.shape[0] + 1]
            if first_table:
                first_table = False
            dfs.append(df)
        tables = dfs

    # Concatenate DataFrames, increasing the number of columns:
    table_data = pd.concat(tables)

    # Create table schema:
    schema = Schema(name=table_name, columns=as_table_columns(table_data),
                    parent=synapse_project_id)

    # Store as Synapse table:
    table = syn.store(Table(schema, table_data))
    synapse_table_id = table.tableId

    return table_data, table_name, synapse_table_id, synapse_project_id


# ============================================================================
# Run above functions to convert all voice files to wav and upload to Synapse:
# ============================================================================
if __name__ == '__main__':

    pass
    # # Setup:
    # synapse_table_id = 'syn4590865'
    # target_synapse_project_id = 'syn4899451'
    # username = ''
    # password = ''
    # column_name = 'audio_audio.wav'
    # download_limit = 3 # Test with first 3 rows or None for all rows
    # out_path = '.'
    # ffmpeg = '/home/arno/software/audio/ffmpeg/ffmpeg'
    # table_name = 'mPower phonation wav files and file handle IDs'
    # #table_name = 'mPower countdown wav files and file handle IDs'
    #
    # # Download files:
    # table_data, files = read_synapse_table_files(synapse_table_id,
    #                                              column_name, download_limit,
    #                                              out_path,
    #                                              username, password)
    #
    # # Upload wav files and file handle IDs:
    # files_to_synapse_table(files, target_synapse_project_id,
    #                                 table_name, username, password)
