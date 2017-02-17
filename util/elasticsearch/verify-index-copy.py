"""
Verifies that an index was correctly copied from one ES host to another.
"""

from itertools import izip

from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan
from argparse import ArgumentParser


description = """
Compare two Elasticsearch indices
"""

SCAN_THRESHOLD = .9

def parse_args():
    """
    Parse the arguments for the script.
    """
    parser = ArgumentParser(description=description)

    parser.add_argument(
        '-o', '--old', dest='old', required=True, nargs=2,
        help='Hostname and index of old ES host, e.g. https://localhost:9200 content'
    )
    parser.add_argument(
        '-n', '--new', dest='new', required=True, nargs=2,
        help='Hostname of new ES host, e.g. https://localhost:9200 content'
    )

    return parser.parse_args()


def main():
    """
    Run the verification.
    """
    args = parse_args()
    old_es = Elasticsearch([args.old[0]])
    new_es = Elasticsearch([args.new[0]])

    old_index = args.old[1]
    new_index = args.new[1]

    old_stats = old_es.indices.stats(index=args.old[1])['indices'][old_index]['total']
    new_stats = new_es.indices.stats(index=args.new[1])['indices'][new_index]['total']

    #compare document count
    old_count = old_stats['docs']['count']
    new_count = new_stats['docs']['count']

    print "{}: Document count ({} = {})".format(
        'OK' if old_count == new_count else 'FAILURE', old_count, new_count
    )

    old_size = old_stats['store']['size_in_bytes']
    new_size = new_stats['store']['size_in_bytes']
    print "{}: Index size ({} = {})".format(
        'OK' if old_count == new_count else 'FAILURE', old_size, new_size
    )

    matching = 0
    total = 0

    # Scan for matching documents
    old_iter = scan(old_es, index=old_index)
    new_iter = scan(new_es, index=new_index)
    for (old_elt, new_elt) in izip(old_iter, new_iter):
        if old_elt['_id'] == new_elt['_id']:
            matching += 1
        total += 1
        if total % 100 == 0:
            print 'processed {} items'.format(total)

    ratio = float(matching)/total
    print "{}: Documents matching ({} out of {}, {}%)".format(
        'OK' if ratio > SCAN_THRESHOLD else 'FAILURE', matching, total, int(ratio * 100)
    )

    # Take subset


"""
index.stats()
elasticsearch.scroll()
use without scan during downtime
elasticsearch.helpers.scan is an iterator (whew)

sample first, then full validation
  is old subset of new?
  is number of edits small?

no numeric ids
can use random scoring?
{"size": 1, "query": {"function_score": {"functions":[{"random_score": {"seed": 123456}}]}}}
use that with scroll and check some number
can't use scroll with sorting. Maybe just keep changing the seed?
  It's kinda slow, but probably fine
  get `size` at a time
  are random sorts going to get the same docs on both clusters?
Alternative: random score with score cutoff? Or script field and search/cutoff
  Might also be able to use track_scores with scan&scroll on 1.5 and a score cutoff
"""

if __name__ == '__main__':
    main()
