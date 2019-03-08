""" Functions to Flatten Predictions """


def flatten_ml_empty_preds(preds_empty):
    """ Flatten Empty Preds """
    return _flatten_ml_empty_confidences(preds_empty)


def flatten_ml_species_preds(preds_species):
    """ Flatten Empty and Species preds """
    flat_species_conf = _flatten_ml_confidences(preds_species)
    flat_species_top = _flatten_ml_toppreds(preds_species)
    return {**flat_species_top, **flat_species_conf}


def _is_binary_label(preds):
    """ Check whether preds are from binary label or not
        {'0': '0.01', '1': '0.99'}
    """
    if len(preds) == 2:
        if ('1' in preds) and ('0' in preds):
            return True
    return False


def _flatten_ml_confidences(preds):
    """ 'aggregated_pred':
            {'empty': {'empty': '0.0030', 'species': '0.9970'}}
    """
    agg_preds = preds['aggregated_pred']
    res = {}
    for label_name, label_preds in agg_preds.items():
        if _is_binary_label(label_preds):
            conf = label_preds['1']
            key = 'machine_confidence_{}'.format(label_name)
            res[key] = conf
        else:
            for pred_label, conf in label_preds.items():
                key = 'machine_confidence_{}_{}'.format(
                    label_name, pred_label)
                res[key] = conf
    return res


def _flatten_ml_toppreds(preds):
    """ Add Prediction Data to Meta-Data """
    top_preds = preds["predictions_top"]
    res = {}
    for pred_label, pred_value in top_preds.items():
        key = 'machine_topprediction_%s' % pred_label
        res[key] = pred_value
    return res


def _flatten_ml_empty_confidences(preds):
    """ Add Empty/or Not predictions """
    empty_preds = preds['aggregated_pred']['empty']
    res = {}
    for empty_cat, conf in empty_preds.items():
        key = 'machine_confidence_{}'.format(empty_cat)
        res[key] = conf
    return res