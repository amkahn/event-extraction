#!/usr/bin/python

# Written by Andrea Kahn
# Last updated Aug. 28, 2014

'''
This script takes as input:
1) A path to the output file, where each line corresponds with a patient and takes the format: MRN [tab] date1 [tab] score1 [tab] date2 [tab] score2 ...
2) A path to the gold data file, where each line corresponds with a patient and takes the format: MRN[tab]gold_date_1[tab]gold_date_2 ...

It then calculates various evaluation metrics and prints them to standard out.
'''

from sys import argv
import logging
from date_candidate import *

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.WARNING)


def main():
    logging.basicConfig()
    
    output_filename = argv[1]
    gold_data_filename = argv[2]
    
    output_file = open(output_filename)
    output_dict = get_output_dict(output_file)
    output_file.close()
    LOG.debug("Here is the output dictionary: %s" % output_dict)
    LOG.debug("%s items in output dictionary" % len(output_dict))

    gold_data_file = open(gold_data_filename)
    gold_data_dict = get_data_dict(gold_data_file)
    gold_data_file.close()
    LOG.debug("Here is the gold data dictionary: %s" % gold_data_dict)
    LOG.debug("%s items in gold data dictionary" % len(gold_data_dict))
    
    print_results(gold_data_dict, output_dict)
#   print_output_comparison(gold_data_dict, output_dict)
#   print_output_not_in_top_n(gold_data_dict, output_dict, 5, 'lenient')


def get_output_dict(file):
    '''
    This method takes as input an open file object and returns a dictionary of MRNs mapped to lists of DateCandidate objects corresponding to the dates returned for that patient.
    '''
    output_dict = {}
    
    for line in file:
        line_elements = line.strip().split('\t')
        MRN = line_elements[0]
#       LOG.debug("MRN is %s" % MRN)
        if not output_dict.get(MRN):
            output_dict[MRN] = []
        
        if len(line_elements) % 2 != 1:
            LOG.warning("Bad output file line format; skipping: %s" % line)
        else:
#           LOG.debug("Processing line: %s" % line)
            for i in xrange(1, len(line_elements), 2):
                date_vals = make_date(line_elements[i])
                if date_vals:
                    date = date_vals[0]
                else:
                    LOG.warning("Could not make date: %s" % line_elements[i])
                    date = None
                score = float(line_elements[i+1])
                candidate = DateCandidate(date, [], score)
                output_dict[MRN].append(candidate)
            
    return output_dict


def get_data_dict(file):
    '''
    This method takes as input an open file object and returns a dictionary of MRNs mapped to lists of Date objects corresponding to the gold dates for that patient for the event being evaluated.
    '''
    data_dict = {}
    
    for line in file:
        line = line.strip()
        tokens = line.split('\t')
        if len(tokens) < 2:
            LOG.warning("Unexpected line format (should be MRN[tab]date ... ); skipping line: %s" % line)
        else:
            MRN = tokens[0]
            for i in xrange(1, len(tokens)):
#               LOG.debug("Trying to make date from: %s" % tokens[i])
                date_vals = make_date(tokens[i])
                if not date_vals:
                    LOG.warning("Could not interpret date expression; skipping line: %s" % line)
                else:
                    if data_dict.get(MRN) == None:
                        data_dict[MRN] = []
                    data_dict[MRN].extend(date_vals)
    
    return data_dict


def print_results(gold_data, sys_output):
    '''
    This method takes as input a hash of MRN mapped to gold dates (Date objects) and a hash of MRNs mapped to lists of DateCandidate objects returned by the system. It then prints various evaluation metrics to standard out.
    '''
    strict_recall, lenient_recall = get_recall(gold_data, sys_output)
    strict_precision, lenient_precision = get_precision(gold_data, sys_output)
    strict_f1 = get_f1_score(strict_recall, strict_precision)
    lenient_f1 = get_f1_score(lenient_recall, lenient_precision)
    strict_rank_eval1, lenient_rank_eval1 = get_rank_eval(gold_data, sys_output, 1)
    strict_rank_eval2, lenient_rank_eval2 = get_rank_eval(gold_data, sys_output, 2)
    strict_rank_eval3, lenient_rank_eval3 = get_rank_eval(gold_data, sys_output, 3)
    strict_rank_eval4, lenient_rank_eval4 = get_rank_eval(gold_data, sys_output, 4)
    strict_rank_eval5, lenient_rank_eval5 = get_rank_eval(gold_data, sys_output, 5)
    strict_tp_scores, strict_fp_scores, lenient_tp_scores, lenient_fp_scores = get_scores(gold_data, sys_output)
    
    print "Strict recall: %s" % strict_recall
    print "Strict precision: %s" % strict_precision
    print "Strict F1 score: %s" % strict_f1
    print "Percentage of patients for whom 1st date returned is strict match: %s" % strict_rank_eval1
    print "Percentage of patients for whom a strict match appears in the top 2 dates returned: %s" % strict_rank_eval2
    print "Percentage of patients for whom a strict match appears in the top 3 dates returned: %s" % strict_rank_eval3
    print "Percentage of patients for whom a strict match appears in the top 4 dates returned: %s" % strict_rank_eval4
    print "Percentage of patients for whom a strict match appears in the top 5 dates returned: %s" % strict_rank_eval5
    print "Scores of dates that are strict matches: %s" % get_mmmm_string(strict_tp_scores)
    print "Scores of dates that are not strict matches: %s" % get_mmmm_string(strict_fp_scores)
    print
    print "Lenient recall: %s" % lenient_recall
    print "Lenient precision: %s" % lenient_precision
    print "Lenient F1 score: %s" % lenient_f1
    print "Percentage of patients for whom 1st date returned is lenient match: %s" % lenient_rank_eval1
    print "Percentage of patients for whom a lenient match appears in the top 2 dates returned: %s" % lenient_rank_eval2
    print "Percentage of patients for whom a lenient match appears in the top 3 dates returned: %s" % lenient_rank_eval3
    print "Percentage of patients for whom a lenient match appears in the top 4 dates returned: %s" % lenient_rank_eval4
    print "Percentage of patients for whom a lenient match appears in the top 5 dates returned: %s" % lenient_rank_eval5
    print "Scores of dates that are lenient matches: %s" % get_mmmm_string(lenient_tp_scores)
    print "Scores of dates that are not lenient matches: %s" % get_mmmm_string(lenient_fp_scores)
    print
    print "No date: %s" % (str(len(get_dateless_patients(gold_data, sys_output))/float(len(gold_data))))
    print "Dates returned per patient: %s" % get_dates_per_patient(sys_output)
    print


def print_output_comparison(gold_data, sys_output):
    '''
    This method takes as input a hash of MRN mapped to gold dates (Date objects), a hash of MRNs mapped to hashes of information about the patient returned by the system, and a string corresponding with the type of date being evaluated.
    For each patient, it prints to standard out: MRN ground_truth extracted_by_sys
    '''
    for MRN in sorted(gold_data.keys()):
        print MRN+'\t'+str([str(x) for x in gold_data[MRN]])+'\t'+str([str(x.date)+' '+str(x.score)+' '+str(x.snippets) for x in sorted(sys_output[MRN], key=lambda d: d.score)])


def print_output_not_in_top_n(gold_data, sys_output, n, measure='strict'):
    '''
    This method takes as input a hash of MRN mapped to gold dates (Date objects), a hash of MRNs mapped to lists of DateCandidate objects returned by the system, an int n, and an optional measure (string 'strict' or 'lenient'; default is 'strict'). It then prints to standard out, for each patient for whom A correct date does not appear in the top n dates returned: MRN ground_truth extracted_by_sys (where extracted_by_sys is all dates returned, including the top n).
    '''
    if measure not in ['strict', 'lenient']:
        LOG.warning("Measure must be 'strict' or 'lenient'; defaulting to 'strict'")
        measure = 'strict'
    
    not_in_top_n = []
    
    for MRN in gold_data:
        returned = sorted(sys_output[MRN], key=lambda candidate: candidate.score, reverse=True)
        
        top_n_returned = returned[:n]
        LOG.debug("Top %s date(s) returned: %s" % (n, [d.date for d in top_n_returned]))

        strict_match = False
        lenient_match = False
        
        for e in gold_data[MRN]:
            
            if e in [d.date for d in top_n_returned]:
                LOG.debug("Gold date %s in top %s date(s) returned" % (e, n))
                strict_match = True
                lenient_match = True

            elif any(e.is_fuzzy_match(d.date) for d in top_n_returned):
                LOG.debug("Gold date %s has lenient match in top %s date(s) returned" % (e, n))
                lenient_match = True
            
        if not lenient_match:
            LOG.debug("No lenient match for MRN %s" % MRN)
            not_in_top_n.append(MRN)
            
        elif measure=='strict' and not strict_match:
            LOG.debug("No lenient match for MRN %s" % MRN)
            not_in_top_n.append(MRN)
                
    for MRN in sorted(not_in_top_n):
        print MRN+'\t'+str([str(x) for x in gold_data[MRN]])+'\t'+str([str(x.date)+' '+str(x.score)+' '+str(x.snippets) for x in sorted(sys_output[MRN], key=lambda d: d.score)])
        if sum([x.score for x in sys_output[MRN]]) - 1.0 > 0.0001:
        	print "Scores do not add up to 1.0 for MRN %s" % MRN


def get_recall(gold_data, sys_output):
    '''
    This method takes as input a hash of MRN mapped to gold dates (Date objects), a hash of MRNs mapped to lists of Date objects, and a string corresponding with the type of date being evaluated. It then returns a 2-tuple of the strict recall and lenient recall, respectively. (Lenient measures count fuzzy Date matches as matches; strict measures only count exact matches as matches.)
    '''
    num_gold = 0
    strict_matches = 0
    lenient_matches = 0

    for MRN in gold_data:
        if gold_data.get(MRN):
            num_gold += len(gold_data[MRN])
            for e in gold_data[MRN]:
                if e in [d.date for d in sys_output[MRN]]:
                    strict_matches += 1
                    lenient_matches += 1
                elif any(e.is_fuzzy_match(d.date) for d in sys_output[MRN]):
                        lenient_matches += 1
    
    if num_gold == 0:
        return (0, 0)
    else:
        return (float(strict_matches)/num_gold, float(lenient_matches)/num_gold)


def get_precision(gold_data, sys_output):
    '''
    This method takes as input a hash of MRN mapped to gold dates (Date objects), a hash of MRNs mapped to lists of Date objects, and a string corresponding with the type of date being evaluated. It then returns a 2-tuple of the strict precision and lenient precision, respectively. (Lenient measures count fuzzy Date matches as matches; strict measures only count exact matches as matches.)
    '''
    num_returned = 0
    strict_matches = 0
    lenient_matches = 0
    
    for MRN in sys_output:
        num_returned += len(sys_output[MRN])
        for d in sys_output[MRN]:
            if gold_data.get(MRN):
                if d.date in gold_data[MRN]:
                    strict_matches += 1
                    lenient_matches += 1
                elif any(d.date.is_fuzzy_match(e) for e in gold_data[MRN]):
                    lenient_matches += 1
    
    if num_returned == 0:
        return (0, 0)
    else:
        return (float(strict_matches)/num_returned, float(lenient_matches)/num_returned)
    

def get_f1_score(recall, precision):
    '''
    This method takes as input floats corresponding with recall and precision, respectively, and returns the F1 score.
    '''
    if (recall + precision) == 0:
        return 0
    else:
        return float(2*recall*precision)/(recall + precision)


def get_rank_eval(gold_data, sys_output, n):
    '''
    This method takes as input a hash of MRN mapped to gold dates (Date objects), a hash of MRNs mapped to lists of Date objects, a string corresponding with the type of date being evaluated, and an int n. It then returns a 2-tuple of the percentage of patients for whom the first, second, ... OR nth date returned is an exact match to A true date, and the percentage of patients for whom the first, second, ... OR nth date returned is a fuzzy match to A true date, respectively.
    '''
    num_patients = len(gold_data)
    
    if num_patients == 0:
        return (1.0, 1.0)
        
    else:
        strict_matches = 0
        lenient_matches = 0

        for MRN in gold_data:
            returned = sorted(sys_output[MRN], key=lambda candidate: candidate.score, reverse=True)
            
            top_n_returned = returned[:n]
            LOG.debug("Top %s date(s) returned: %s" % (n, [d.date for d in top_n_returned]))
            
            for e in gold_data[MRN]:

                if e in [d.date for d in top_n_returned]:
                    LOG.debug("Gold date %s in top %s date(s) returned" % (e, n))
                    strict_matches += 1
                    lenient_matches += 1
                    LOG.debug("Updated strict matches to %s" % strict_matches)
                    LOG.debug("Updated lenient matches to %s" % lenient_matches)

                elif any(e.is_fuzzy_match(d.date) for d in top_n_returned):
                    LOG.debug("Gold date %s has fuzzy match in top %s date(s) returned" % (e, n))
                    lenient_matches += 1
                    LOG.debug("Updated lenient matches to %s" % lenient_matches)
                    
        return (float(strict_matches)/num_patients, float(lenient_matches)/num_patients)


def get_scores(gold_data, sys_output):
    '''
    This method takes as input a hash of MRN mapped to gold dates (Date objects), a hash of MRNs mapped to lists of Date objects, a string corresponding with the type of date being evaluated, and returns a tuple of four lists: of the scores of DateCandidates returned that are strict matches, of the scores of DateCandidates returned that are not strict matches, of the scores of DateCandidates returned that are lenient matches, and of the scores of DateCandidates returned that are not lenient matches, respectively.
    '''
    strict_tp_scores = []
    strict_fp_scores = []
    lenient_tp_scores = []
    lenient_fp_scores = []
    
    for MRN in sys_output:
        for d in sys_output[MRN]:
            if gold_data.get(MRN):
                if d.date in gold_data[MRN]:
                    strict_tp_scores.append(d.score)
                    lenient_tp_scores.append(d.score)
                elif any(d.date.is_fuzzy_match(e) for e in gold_data[MRN]):
                    strict_fp_scores.append(d.score)
                    lenient_tp_scores.append(d.score)
                else:
                    strict_fp_scores.append(d.score)
                    lenient_fp_scores.append(d.score)
    
    return (strict_tp_scores, strict_fp_scores, lenient_tp_scores, lenient_fp_scores)


def get_dateless_patients(gold_data, sys_output):
    '''
    This method takes as input a hash of MRN mapped to gold dates (Date objects) and a hash of MRNs mapped to DateCandidates returned by the system for that patient, and returns a list of MRNs for patients for whom no date is returned.
    '''
    dateless = []
    for MRN in sys_output:
        # If there exist gold-standard dates for this event for this patient
        if gold_data[MRN]:
            if not sys_output[MRN]:
                dateless.append(MRN)
    return dateless


def get_dates_per_patient(sys_output):
    '''
    This method takes as input a hash of MRNs mapped to hashes of information about the patient returned by the system; calculates the minimum, maximum, mean, and median dates returned per patient; and returns a string containing this information.
    '''
    num_dates = []
    for MRN in sys_output:
        num_dates.append(len(sys_output[MRN]))
        
    return get_mmmm_string(num_dates)


def get_mmmm_string(input_list):
    '''
    This method takes a list of ints or floats; calculates the minimum, maximum, mean, and median dates returned per patient; and returns a string containing this information.
    '''
    return 'Min %s; Max %s; Mean %s; Median %s' % (min(input_list), max(input_list), float(sum(input_list))/len(input_list), get_median(input_list))


def get_median(list):
    '''
    This function takes a list of values as input and returns the median value.
    '''
    list = sorted(list)
    
    if len(list) % 2 == 0:
        median = (list[int(len(list)/2.0)] + list[int(len(list)/2.0)-1])/2.0
    else:
        median = list[int(len(list)/2.0)]
    
    return median



if __name__=='__main__':
    main()