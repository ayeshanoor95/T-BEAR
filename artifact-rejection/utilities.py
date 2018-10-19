import matplotlib.pyplot as plt
import mne
import numpy as np
import pandas as pd

from matplotlib import style
from pathlib import Path
from scipy.io import loadmat
from sklearn import svm
from sklearn.ensemble import IsolationForest
from sklearn.metrics import accuracy_score
from sklearn.metrics import classification_report
style.use("ggplot")


def load_subject_dir(file_path, mat_reject, mat_stage):
    """Loads file paths for EEG data and MATLAB auxiliaries and returns those files.

    Arguments:
        file_path (str): The file path to the .set file.
        mat_stage (str): The file path to the MATLAB file with sleep stages.
        mat_reject (str): The file path to the MATLAB file/array with labels for epoch rejects.

    Returns:
        dict: Returns a dictionary containing all files that did not error.

    Examples:
        >>> files = load_subject_dir(file_path, mat_stage, mat_reject)
        >>> files.keys()
        dict_keys(['epochs', 'stages', 'reject'])
    """
    files = dict()
    found_set, found_sleep, found_reject = True, True, True
    try:
        set_file = mne.io.read_epochs_eeglab(file_path)
        files['epochs'] = set_file
    except:
        set_file = mne.io.read_raw_eeglab(file_path)
        files['epochs'] = set_file
    else:
        pass

    try:
        sleep_file = loadmat(mat_stage)
        sleep = sleep_file['stages'].flatten()
        files['stages'] = sleep
    except FileNotFoundError:
        found_sleep = False
        pass

    try:
        reject_file = loadmat(mat_reject)
        rejects = reject_file['reject'].flatten()
        rejects_ = resize_reject(rejects)
        files['reject'] = rejects_
    except FileNotFoundError:
        found_reject = False
        pass

    if not found_set:
        print("ERROR: .set file was not found.")
    if not found_sleep:
        print("WARNING: Sleep stages file was not found.")
    if not found_reject:
        print("NOTE: Reject file was not found.")

    return files


def clean_df(df):
    """Cleans dataframe by reseting index, deleting non-essential features, etc.

    Arguments:
        df (DataFrame): The freshly converted dataframe.

    Returns:
        DataFrame: Returns a dataframe containing all files that did not error.
    """
    print("Cleaning data...")

    try:
        df = df.drop(['condition'], axis=1)
    except:
        pass

    columns, df = sorted(list(df.columns)), df.reset_index()
    cleaned_columns = ['time']
    if 'epoch' in list(df.columns):
        cleaned_columns += ['epoch']

    cleaned_columns += columns
    df = df[cleaned_columns]

    try:
        df[['time', 'epoch']] = df[['time', 'epoch']].astype(int)
    except:
        pass

    print("Cleaned data successfully!\n")
    return df


def resize_reject(reject_array, r=2000):
    repeated_reject_array = np.repeat(reject_array, r)
    return repeated_reject_array


def extract_df_values(df):
    df_ = df.copy()
    print("Preparing data for classification...")
    value_columns = list(df.columns)

    try:
        if 'time' in value_columns:
            value_columns.remove('time')
        if 'epoch' in value_columns:
            value_columns.remove('epoch')
    except:
        pass

    df_values = df_[value_columns]
    print("Data prepared successfully!\n")
    return df_values

def run_IForest(df_, df_values, reject):
    print("Running IForest algorithm...")
    X = df_values
    clfIF = IsolationForest(n_estimators=80, max_samples='auto', contamination=0.001,
                            bootstrap=False, n_jobs=3, random_state=42, verbose=1)
    clfIF.fit(X)

    pred_artifacts = clfIF.predict(X)
    count_artifacts = np.unique(ar=pred_artifacts, return_counts=True)
    index_artifacts = [i for i, x in enumerate(pred_artifacts) if x == -1]

    df_IF = df_.loc[index_artifacts]
    df_IF_epochs = set(df_IF['epoch'])
    print(df_IF_epochs)

    num_artifacts_pair = count_artifacts[1][0]
    num_artifacts = num_artifacts_pair[1][1]

    total_pts = count_artifacts[1][1]
    total_artifacts = np.count_nonzero(reject)
    print("IForest algorithm ran successfully!\n")
    print(set(df_IF['epoch']))
