"""Explicit coefficient-source selection shared by Q7 and Q8 consumers."""
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parents[3]/'outputs/sideproject_q5w_wsindy'
KEYS = ['system_id', 'source_initial_condition_set', 'noise_sigma', 'subsample_rho', 'noise_realization', 'q5w_configuration']
SOURCE = 'matlab_original_72d8d6e'


def uniform_rows(frame):
    arm = frame.q5w_configuration.str.split(':').str[0]
    return ((arm == 'W1') & (frame.subsample_rho == 0)) | ((arm == 'W1-interp') & (frame.subsample_rho == .5))


def select_rows(port, source='matlab', matlab_inputs=None):
    """Replace only original-backed arms, retaining every supplied port-only row."""
    port = port.copy()
    if 'source_initial_condition_set' not in port:
        port = port.rename(columns={'initial_condition_set':'source_initial_condition_set'})
    if port.duplicated(KEYS).any():
        raise ValueError('Duplicate Q5-W input rows')
    if source == 'port':
        if 'q5w_coefficient_source' in port and not port.q5w_coefficient_source.fillna('port').eq('port').all():
            raise ValueError('Legacy mode requires port inputs')
        port['q5w_coefficient_source'] = 'port'
        return port
    if source != 'matlab':
        raise ValueError('Unknown Q5-W coefficient source')
    paths = matlab_inputs if matlab_inputs is not None else [BASE/'full_matlab/details.csv', BASE/'w1_interp_full_matlab/details.csv']
    frames = []
    for path in paths:
        path = Path(path)
        control = path.parent/'controls.json'
        import json
        if not control.exists() or not json.loads(control.read_text()).get('complete'):
            raise ValueError('MATLAB row controls are incomplete: '+str(control))
        frames.append(pd.read_csv(path, low_memory=False, float_precision='round_trip'))
    matlab = pd.concat(frames, ignore_index=True)
    if (matlab.duplicated(KEYS).any() or not uniform_rows(matlab).all()
            or not matlab.q5w_coefficient_source.eq(SOURCE).all()):
        raise ValueError('Invalid MATLAB source rows')
    lookup = matlab.set_index(KEYS, drop=False)
    expected = port.loc[uniform_rows(port)]
    selected = []
    for row in expected.to_dict('records'):
        key = tuple(row[k] for k in KEYS)
        if key not in lookup.index:
            raise ValueError('Missing MATLAB replacement row: '+str(key))
        replacement = lookup.loc[key]
        if replacement.observed_data_sha256 != row['observed_data_sha256']:
            raise ValueError('MATLAB replacement observed hash differs')
        selected.append(replacement.to_dict())
    other = port.loc[~uniform_rows(port)].copy()
    other['q5w_coefficient_source'] = 'port'
    return pd.concat([other, pd.DataFrame(selected)], ignore_index=True)


def known_cost(group, field):
    """Missing original counts must remain unavailable, including mixed groups."""
    values = pd.to_numeric(group[field], errors='coerce')
    return int(values.sum()) if values.notna().all() else None
