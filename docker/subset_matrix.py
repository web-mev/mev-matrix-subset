#! /usr/bin/python3

import sys
import os
import json
import pandas as pd
import argparse


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('-i', '--input', \
        required=True, \
        dest = 'input_matrix',
        help='The input matrix'
    )

    parser.add_argument('-s', '--samples', \
        required=False, \
        dest = 'cols',
        help=('A comma-delimited list of sample/column names.'
        )
    )

    parser.add_argument('-f', '--features', \
        required=False, \
        dest = 'rows',
        help=('A comma-delimited list of feature/row names.'
        )
    )

    parser.add_argument('--keepcols',
        action = 'store_true'
    )

    parser.add_argument('--keeprows',
        action = 'store_true'
    )

    args = parser.parse_args()
    return args

def write_error_message(direction, diff_list, threshold=5):
    '''
    `direction` is a string (e.g. "columns" or "rows")
    and `diff_list` is a list of sample/col or gene/row IDs
    `threshold` determines how many problem samples to report
    so that the error message is not too overwhelming.
    '''
    if len(diff_list) == 1:
        msg = ('One of your selections ("{s}") was not found'
            ' in the {direction} of your matrix.').format(
                direction=direction,
                s = diff_list[0]
            )
    else:
        extra_text = ','.join(diff_list[:threshold])
        if len(diff_list) > threshold:
            extra_text += ' (and {n} others)'.format(n=len(diff_list)- threshold)
        msg = ('Some of your selections were not found'
            ' in the {direction} of your matrix: {extra}').format(
                direction=direction,
                extra = extra_text
            )
    return msg
    
if __name__ == '__main__':
    args = parse_args()
    # args is like Namespace(
    #    cols='a,b,c', 
    #    input_matrix='foo.tsv', 
    #    keepcols=True, 
    #    keeprows=False, 
    #    rows=None)

    df = pd.read_table(args.input_matrix, sep='\t', index_col=0)

    # First remove columns/samples (if any specified)
    # If cols was not specified, then we ignore the 'keepcols'
    # option. Otherwise we would end up with empty subsets
    if args.cols:
        columns = [x.strip() for x in args.cols.split(',')]
        diff_set = set(columns).difference(set(df.columns))
        if len(diff_set) > 0:
            sys.stderr.write(write_error_message(
                'columns',
                list(diff_set),
            ))
            sys.exit(1)

        # actually perform the column subset
        if args.keepcols:
            df = df[columns]
        else:
            other_cols = list(set(df.columns).difference(columns))
            df = df[other_cols]

    if args.rows:
        rows = [x.strip() for x in args.rows.split(',')]
        diff_set = set(rows).difference(set(df.index))
        if len(diff_set) > 0:
            sys.stderr.write(write_error_message(
                'rows',
                list(diff_set),
            ))
            sys.exit(1)

        # actually perform the row subset
        row_idx = df.index.isin(rows)
        if args.keeprows:
            df = df.loc[row_idx]
        else:
            df = df.loc[~row_idx]

    if all(df.shape):
        working_dir = os.path.dirname(args.input_matrix)
        fout = os.path.join(working_dir, 'reduced_matrix.tsv')
        df.to_csv(fout, sep='\t')
        outputs = {
            'reduced_matrix': fout
        }
        json.dump(outputs, open(os.path.join(working_dir, 'outputs.json'), 'w'))
    else:
        if df.shape[0] == 0:
            sys.stderr.write('After subsetting, there were zero rows remaining.'
                ' No output file was created.')
            sys.exit(1)
        if df.shape[1] == 0:
            sys.stderr.write('After subsetting, there were zero columns remaining.'
                ' No output file was created.')
            sys.exit(1)