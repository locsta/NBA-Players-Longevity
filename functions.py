import seaborn as sns
import numpy as np
import pandas as pd
import itertools
import matplotlib.pyplot as plt
from sklearn.metrics import precision_score, recall_score, accuracy_score, f1_score
from sklearn.metrics import roc_curve, auc
from sklearn.metrics import confusion_matrix
from sklearn.tree import export_graphviz
from IPython.display import Image  
from pydotplus import graph_from_dot_data
from xgboost import plot_tree
from pprint import pprint
from sklearn.neighbors import KNeighborsClassifier

def plot_confusion_matrix(labels, preds_proba, classes, threshold=0.5, normalize=False, title='Confusion matrix', cmap=plt.cm.Blues):
    """Calculate the confusion matrix for a determined threshold and plot it in a nicely formatted way

    Parameters:
    labels (list): List of labels (class)
    preds_proba (list): List of predicted probabilities
    threshold (float): Threshold
    normalize (bool): normalize True will will plot using percentages, normalize False will plot using raw values
    title (str): Plot's title
    cmap (str): Color Map
    return_cm (bool): return the non-normalised confusion matrix if set to True


    Returns:
    float:Threshold optimal value

   """
    preds = preds_proba_to_preds_class(preds_proba,threshold)
    cm_std = confusion_matrix(labels, preds)
    # Check if normalize is set to True
    # If so, normalize the raw confusion matrix before visualizing
    if normalize:
        cm = cm_std.astype('float') / cm_std.sum(axis=1)[:, np.newaxis]
        print("Normalized confusion matrix")
    else:
        cm = cm_std
        print('Confusion matrix, without normalization')

    print(cm)

    plt.imshow(cm, cmap=cmap)
    
    # Add title and axis labels 
    plt.title(title)
    plt.ylabel('True label')
    plt.xlabel('Predicted label')
    
    # Add appropriate axis scales
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=45)
    plt.yticks(tick_marks, classes)
    
    # Text formatting
    fmt = '.2f' if normalize else 'd'
    # Add labels to each cell
    thresh = cm.max() / 2.
    # Here we iterate through the confusion matrix and append labels to our visualization 
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, format(cm[i, j], fmt),
                 horizontalalignment='center',
                 color='white' if cm[i, j] > thresh else 'black')
    
    # Add a legend
    plt.colorbar()
    plt.show()
    return cm_std
    
def find_best_k(X_train, y_train, X_test, y_test, min_k=1, max_k=25):
    """Find the best value for K in a certain range of values for KNeighborsClassifier

    Parameters:
    X_train (float): The percentage of positives in the population
    y_train (float): The Cost of false positives minus the cost of true negatives
    X_test (float): The Cost of false negatives minus the cost of true positives
    y_test (float): True positive rate
    min_k (float): Minimum value for K
    max_k (float): Maximum value for K


    Returns:
    int: Best value for K

   """
    best_k = 0
    best_score = 0.0
    for k in range(min_k, max_k+1, 2):
        knn = KNeighborsClassifier(n_neighbors=k)
        knn.fit(X_train, y_train)
        preds = knn.predict(X_test)
        f1 = f1_score(y_test, preds)
        if f1 > best_score:
            best_k = k
            best_score = f1
    print("Best Value for k: {}".format(best_k))
    print("F1-Score: {}".format(best_score))

def preds_proba_to_preds_class(preds_proba,threshold):
    """Transform prediction probabilities into classes (booleans) using a determined threshold

    Parameters:
    preds_proba (list): List of probabilities
    threshold (float): Threshold

    Returns:
    classes (list): List of classes

   """
    return [True if pred > threshold else False for pred in preds_proba]

def threshold_selection(prevalence, CostFP_minus_CostTN, CostFN_minus_CostTP, y, y_hat):
    """Calculate the optimal treshold depending on prevalence, costs, true positive rates and false positive rates
    
    Args:
        prevalence (float): The percentage of positives in the population
        CostFP_minus_CostTN (float): The cost of false positives minus the cost of true negatives
        CostFN_minus_CostTP (float): The cost of false negatives minus the cost of true positives
        y (list): True labels (classes)
        y_hat (list): Predicted proba for labels (classes)
    
    Returns:
        [float]: Best threshold
    """
    fpr, tpr, thresholds = roc_curve(y, y_hat)
    m = ((1 - prevalence) / prevalence) * ((CostFP_minus_CostTN) / (CostFN_minus_CostTP))
    fm_thresholds = []
    for i in range(len(fpr)):
        fm = tpr[i] - (m * fpr[i])
        fm_thresholds.append((thresholds[i], fm))
    fm_thresholds = sorted(fm_thresholds, key=lambda fm_value: fm_value[1], reverse=True)
    return fm_thresholds[0][0]

def metrics(labels, preds_proba, print_metrics=True, plot=False, threshold=0.5, rounded=4):
    """Plot the ROC curve, calculate and print AUC, Precision, Recall, Accuracy and F1 scores

    Parameters:
    labels (list): List of labels (classes)
    preds_proba (list): List of predicted probabilities
    print_metrics (bool): Print the metrics if parameter set to True
    plot (bool): Plot the ROC curve if parameter set to True
    threshold (float): Threshold (purely as information)
    rounded (int): The number of digits for the scores


    Returns:
    scores (dict): Return a dictionnary of scores (AUC, Precision, Recall, Accuracy and F1)

   """
    

    test_fpr, test_tpr, test_thresholds = roc_curve(labels, preds_proba)
    roc_auc = auc(test_fpr, test_tpr)
    preds = preds_proba_to_preds_class(preds_proba,threshold)
    precision = precision_score(labels, preds)
    recall = recall_score(labels, preds)
    accuracy = accuracy_score(labels, preds)
    f1 = f1_score(labels, preds)
    if plot:
        sns.set_style('darkgrid', {'axes.facecolor': '0.9'})
        plt.figure(figsize=(10, 8))
        lw = 2
        plt.plot(test_fpr, test_tpr, color='darkorange',
                lw=lw, label='ROC curve')
        plt.plot([0, 1], [0, 1], color='navy', lw=lw, linestyle='--')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.yticks([i/20.0 for i in range(21)])
        plt.xticks([i/20.0 for i in range(21)])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('Receiver operating characteristic (ROC) Curve')
        plt.legend(loc='lower right')
        plt.show()
    if print_metrics:
        print(f"ROC AUC Score: {roc_auc}\n")
        print(f"------- Metrics for threshold {threshold} -------")
        print(f"- Precision Score: {precision}")
        print(f"- Recall Score: {recall}")
        print(f"- Accuracy Score: {accuracy}")
        print(f"- F1 Score: {f1}\n")
    else:
        return {"roc_auc":roc_auc, "precision":precision, "recall":recall, "accuracy":accuracy, "f1":f1}


def get_roc_auc(y_test, y_hat_test):
    """Return the ROC AUC value

    Parameters:
    y_test (list): Target Labels
    y_hat_test (list): Predicted target labels

    Returns:
    float:Area Under The Curve pof Receiver Operating Characteristics

   """
    test_fpr, test_tpr, test_thresholds = roc_curve(y_test, y_hat_test)
    roc_auc = auc(test_fpr, test_tpr)
    return roc_auc

def print_corr(df, pct=0):
    """Prints the multicollinearity heatmap with the option of setting a minimum multicollinearity percentage

    Parameters:
    df (pandas dataframe): Pandas DataFrame
    pct (float): Optional minimum multicollinearity percentage (multicollinearity lower than the value of the variable "pct" will not be shown)

    Returns:
    void:This function does not return values

   """
    
    sns.set(style="white")

    # Compute the correlation matrix
    if pct == 0:
        corr = df.corr()
    else:
        corr = abs(df.corr()) > pct

    # Generate a mask for the upper triangle
    mask = np.zeros_like(corr, dtype=np.bool)
    mask[np.triu_indices_from(mask)] = True

    # Set up the matplotlib figure
    f, ax = plt.subplots(figsize=(11, 9))

    # Generate a custom diverging colormap
    cmap = sns.diverging_palette(220, 10, as_cmap=True)

    # Draw the heatmap with the mask and correct aspect ratio
    sns.heatmap(corr, mask=mask, cmap=cmap, vmax=1, center=0, square=True, linewidths=.5, cbar_kws={"shrink": .5})

def opt_plots_xgb(opt_model):
    """XGBoost model: Plot scores with different parameter selections
    """
    opt = pd.DataFrame(opt_model.cv_results_)
    cols = [col for col in opt.columns if ('mean' in col or 'std' in col) and 'time' not in col]
    params = pd.DataFrame(list(opt.params))
    opt = pd.concat([params,opt[cols]],axis=1,sort=False)
    
    f, axes = plt.subplots(3, 2, figsize=(12, 7))
    # f.subplots_adjust(top = 0.99, bottom=0.01, hspace=1.5, wspace=0.4)
    f.tight_layout(h_pad=4, w_pad=4)
    sns.heatmap(pd.pivot_table(opt,index='xgb__n_estimators',columns='xgb__learning_rate',values='mean_train_score')*100, ax=axes[0, 0])
    axes[0, 0].set_title('ROC_AUC - Training')
    sns.heatmap(pd.pivot_table(opt,index='xgb__n_estimators',columns='xgb__learning_rate',values='mean_test_score')*100, ax=axes[0, 1])
    axes[0, 1].set_title('ROC_AUC - Validation')
    sns.heatmap(pd.pivot_table(opt,index='xgb__max_depth',columns='xgb__subsample',values='mean_train_score')*100, ax=axes[1, 0])
    axes[1, 0].set_title('ROC_AUC - Training')
    sns.heatmap(pd.pivot_table(opt,index='xgb__max_depth',columns='xgb__subsample',values='mean_test_score')*100, ax=axes[1, 1])
    axes[1, 1].set_title('ROC_AUC - Validation')
    sns.heatmap(pd.pivot_table(opt,index='xgb__gamma',columns='xgb__min_child_weight',values='mean_train_score')*100, ax=axes[2, 0])
    axes[2, 0].set_title('ROC_AUC - Training')
    sns.heatmap(pd.pivot_table(opt,index='xgb__gamma',columns='xgb__min_child_weight',values='mean_test_score')*100, ax=axes[2, 1])
    axes[2, 1].set_title('ROC_AUC - Validation')