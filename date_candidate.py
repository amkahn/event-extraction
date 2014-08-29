#!/usr/bin/python

# Written by Andrea Kahn
# Last updated Aug. 28, 2014


import logging
import re
from date import *

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.WARNING)


class DateCandidate(object):
    '''
    A DateCandidate object stores a Date object, a list of supporting snippets (which are themselves strings), and a confidence score (default is 0).
    '''

    def __init__(self, date, snippets, score=0):
        self.date = date
        self.snippets = snippets
        self.score = score

    def __repr__(self):
        to_return = "DATE: %s\nSCORE: %s\nSNIPPETS: %s\n" % (self.date, self.score, self.snippets)
        return to_return

    def combine_candidate(self, other):
        '''
        This method takes another DateCandidate as input and combines it with this one (i.e., adding the scores and concatenating the snippets lists), preserving the date field of this one.
        '''
        LOG.debug("Combining DateCandidate %s with DateCandidate %s; preserving Date of the former" % (self, other))
        self.snippets.extend(other.snippets)
        self.score += other.score

    
def rerank_candidates(candidates, filter, n):
    '''
    This method takes as input a list of date candidates and collapses them and scores them.
    '''
    LOG.debug("List is now length %s (beginning of reranking)" % len(candidates))
#   remove_duplicate_candidates(candidates) # add back in when rework fuzzy date resolution
    score_candidates(candidates)
    remove_fuzzy_dates(candidates)
    LOG.debug("List is now length %s (after collapsing fuzzy dates)" % len(candidates))
#   top_n_candidates(candidates, n)
#   filter_candidates(candidates, filter)
    filter_candidates_keep_top_n(candidates, filter, n)
    LOG.debug("List is now length %s (after filtering)" % len(candidates))


def split_candidate(fuzzy_candidate, precise_candidate_list):
    '''
    This method takes as input a single DateCandidate and a list of DateCandidates, divides the score of the single candidate among the candidates in the list proportionally according to their scores, and augments their scores accordingly. It is intended to be used to collapse a fuzzy candidate across multiple more-precise matches. Snippets from the single candidate are appended to the snippets list of every candidate in the list.
    '''
    LOG.debug("Candidate to split: %s" % fuzzy_candidate)
    LOG.debug("Candidates to split among: %s" % precise_candidate_list)
    norm_constant = sum([candidate.score for candidate in precise_candidate_list])
    LOG.debug("Normalization constant is: %s" % norm_constant)
    if norm_constant:
        for candidate in precise_candidate_list:
            candidate.score += fuzzy_candidate.score * float(candidate.score)/norm_constant
            candidate.snippets.extend(fuzzy_candidate.snippets)
    else:
        for candidate in precise_candidate_list:
            candidate.score += fuzzy_candidate.score * float(candidate.score)/len(precise_candidate_list)
            candidate.snippets.extend(fuzzy_candidate.snippets)


def score_candidates(candidate_list):
    '''
    FIXME: Add more advanced reasoning, e.g. take into account prior score (may actually want two scores, the prior score and a new confidence level)
    This method takes as input a list of DateCandidate objects, sets their scores (where the score is the number of supporting snippets for this candidate divided by the sum of the number of supporting snippets for all candidates in the list), and returns a list of the scored objects.
    '''

    total_snippets = sum([len(c.snippets) for c in candidate_list])
    LOG.debug("%s total snippets" % total_snippets)

    for candidate in candidate_list:
        score = len(candidate.snippets)/float(total_snippets)
        LOG.debug("Score is %s" % score)
        candidate.score = score

    if sum([x.score for x in candidate_list])-1 > 0.001:
        LOG.warning("Candidate scores do not add up to 1")


def filter_candidates(candidate_list, threshold_score):
    '''
    This method takes as input a list of DateCandidate objects and a threshold score, and removes all candidates whose scores do not meet some minimum threshold.
    '''
    for i in xrange(len(candidate_list)-1, -1, -1):
        if candidate_list[i].score < threshold_score:
            LOG.debug("Removing candidate number %s with score %s" % (i, candidate_list[i].score))
            del candidate_list[i]

        else:
            LOG.debug("Keeping candidate number %s with score %s" % (i, candidate_list[i].score))


def top_n_candidates(candidate_list, n):
    '''
    This method takes as input a list of DateCandidate objects, sorts them in descending order by score, and removes all but the top n candidates.
    '''
    if len(candidate_list) > n:
        candidate_list.sort(key=lambda candidate: candidate.score, reverse=True)
        for i in xrange(len(candidate_list)-1, n-1, -1):
            LOG.debug("Deleting candidate number %s in list" % i)
            del candidate_list[i]

    LOG.debug("List is now length %s" % len(candidate_list))


def filter_candidates_keep_top_n(candidate_list, threshold_score, n):
    '''
    This method takes as input a list of DateCandidate objects, a threshold score, and an int n; sorts the list of candidates in descending order by score; and starting from the end of the list, removes all candidates whose scores do not meet some minimum threshold, stopping if the list hits length n.
    '''
    if n < 0:
        LOG.warning("n must be 0 or greater (input: %s); cannot perform filtering" % n)

    elif len(candidate_list) > n:
        LOG.debug("Filtering candidate list of length %s" % len(candidate_list))
        candidate_list.sort(key=lambda candidate: candidate.score, reverse=True)

        next_score = candidate_list[-1].score
        LOG.debug("Lowest-scored candidate has score %s" % next_score)
        LOG.debug("Highest-scored candidate has score %s" % candidate_list[0].score)
        i = len(candidate_list)-1
        
        while (next_score < threshold_score) and (i >= n):
            LOG.debug("Removing candidate number %s with score %s" % (i, next_score))
            del candidate_list[i]
            i -= 1
            if i >= 0:
                next_score = candidate_list[i].score


def remove_fuzzy_dates(candidate_list):
    '''
    This method takes as input a list of DateCandidate objects. It begins by combining any DateCandidate objects whose 'date' fields are identical. Then, DateCandidates whose 'date' field is a fuzzy date that could represent a precise date of one and only one* other DateCandidate in the list are combined with the more precise DateCandidate object.
    *NB: The list [May 5, 2008, May 2008, 2008] will get collapsed to [May 5, 2008]
    '''
    remove_duplicate_candidates(candidate_list)
    # Start with month-year dates, so that [May 5, 2008; May 2008; 2008] will get collapsed to [May 5, 2008]
    # (If start with year-only, 2008 will not get collapsed since there are two potential candidates with which it could be collapsed--even though one is merely a less precise version of the other--and the system will return [May 5, 2008; 2008])
    remove_month_year_dates(candidate_list)
    remove_year_only_dates(candidate_list)


def remove_duplicate_candidates(candidate_list):
    '''
    This method takes as input a list of DateCandidate objects and combines DateCandidate objects whose dates are identical.
    '''
    LOG.debug("Removing duplicate candidates from the following list: %s" % candidate_list)
    for i in xrange(len(candidate_list)-1, -1, -1):
        for j in xrange(i-1, -1, -1):
            LOG.debug("Comparing element %s with element %s" % (i, j))
            if candidate_list[i].date==candidate_list[j].date:
                LOG.debug("Combining candidate %s in list into candidate %s in list" % (i, j))
                candidate_list[j].combine_candidate(candidate_list[i])
                LOG.debug("Removing element %s" % i)
                del candidate_list[i]
                break


def remove_year_only_dates(candidate_list):
    '''
    This method takes as input a list of DateCandidate objects. DateCandidates whose 'date' field is just a year that could represent a precise date of one and only one other DateCandidate in the list are combined with the more precise DateCandidate object.
    '''
    LOG.debug("Removing year-only dates from the following list: %s" % candidate_list)
    for i in xrange(len(candidate_list)-1, -1, -1):
        # If the date is just a year
        if not candidate_list[i].date.month_known:
        
            # Start at the end of the list and look for candidates whose dates could be a more precise version of this one
            LOG.debug("Looking for a more precise version of element %s, %s" % (i, candidate_list[i]))
            matches = []
            for j in xrange(len(candidate_list)-1, -1, -1):
                if (candidate_list[j].date.month_known and candidate_list[i].date.is_fuzzy_match(candidate_list[j].date)):
                    matches.append(candidate_list[j])
            
            if matches:
                # If there's one and only one match, combine the candidates
                if len(matches)==1:
#                   print "Combining %s and %s" % (candidate_list[i], candidate_list[j])
                    matches[0].combine_candidate(candidate_list[i])

                else:
                    split_candidate(candidate_list[i], matches)
                
                del candidate_list[i]
                LOG.debug("Here is the precise date list now: %s" % candidate_list)


def remove_month_year_dates(candidate_list):
    '''
    This method takes as input a list of DateCandidate objects. DateCandidates whose 'date' field is just a year that could represent a precise date of one and only one other DateCandidate in the list are combined with the more precise DateCandidate object.
    '''
    for i in xrange(len(candidate_list)-1, -1, -1):
        # If the date is a month and year only
        if (candidate_list[i].date.month_known and not candidate_list[i].date.day_known):
        
            # Look for candidates whose dates could be a more precise version of this one
            LOG.debug("Looking for a more precise version of %s" % candidate_list[i])
            matches = []
            for j in xrange(len(candidate_list)-1, -1, -1):
                if (candidate_list[j].date.day_known and candidate_list[i].date.is_fuzzy_match(candidate_list[j].date)):
                    LOG.debug("Found match with known day: %s" % candidate_list[j].date)
                    matches.append(candidate_list[j])
            
            # If there's one and only one match, combine the candidates
            if matches:
                if len(matches)==1:
                    LOG.debug("Combining %s and %s" % (candidate_list[i], matches[0]))
                    matches[0].combine_candidate(candidate_list[i])
                else:
                    split_candidate(candidate_list[i], matches)
                del candidate_list[i]
                LOG.debug("Here is the precise date list now: %s" % candidate_list)


def remove_year_only_dates_2(candidate_list):
    '''
    This method takes as input a list of DateCandidate objects. DateCandidates whose 'date' field is just a year that could represent a precise date of one and only one other DateCandidate in the list are combined with the more precise DateCandidate object.
    '''
    LOG.debug("Removing year-only dates from the following list: %s" % candidate_list)
    for i in xrange(len(candidate_list)-1, -1, -1):
        # If the date is just a year
        if not candidate_list[i].date.month_known:
        
            # Start at the end of the list and look for candidates whose dates could be a more precise version of this one
            LOG.debug("Looking for a more precise version of element %s, %s" % (i, candidate_list[i]))
            matches = []
            for j in xrange(len(candidate_list)-1, -1, -1):
                if (candidate_list[j].date.month_known and candidate_list[i].date.is_fuzzy_match(candidate_list[j].date)):
                    matches.append(candidate_list[j])
            
            if matches:
                # If there's one and only one match, combine the candidates
                if len(matches)==1:
#                   print "Combining %s and %s" % (candidate_list[i], candidate_list[j])
                    candidate_list[j].combine_candidate(candidate_list[i])
                    del candidate_list[i]

                else:
                    LOG.debug("Matches: %s" % matches)
                    month_year_matches = filter(lambda x: x.date.day_known==False, matches)
                    LOG.debug("Found %s month/year matches" % len(month_year_matches))
                    if len(month_year_matches) > 1:
                        LOG.warn("Found more than one month/year match: %s" % month_year_matches)
                    
                    # If matches are all fuzzy matches for one another (e.g., ["May 2008", "May 3, 2008", "May 5, 2008"]), candidate in question should get combined with the month/year candidate (e.g., "2008" should get combined with "May 2008" in this case)
                    elif len(month_year_matches) > 0 and all(match1.date.is_fuzzy_match(match2.date) for match1 in month_year_matches for match2 in matches):

    #                   print "Combining %s and %s" % (candidate_list[i], month_year_matches[0])
                        month_year_matches[0].combine_candidate(candidate_list[i])
                        del candidate_list[i]


def remove_month_year_dates_2(candidate_list):
    '''
    This method takes as input a list of DateCandidate objects. DateCandidates whose 'date' field is just a year that could represent a precise date of one and only one other DateCandidate in the list are combined with the more precise DateCandidate object.
    '''
    for i in xrange(len(candidate_list)-1, -1, -1):
        # If the date is a month and year only
        if (candidate_list[i].date.month_known and not candidate_list[i].date.day_known):
        
            # Look for candidates whose dates could be a more precise version of this one
            LOG.debug("Looking for a more precise version of %s" % candidate_list[i])
            matches = []
            for j in xrange(len(candidate_list)-1, -1, -1):
                if (candidate_list[j].date.day_known and candidate_list[i].date.is_fuzzy_match(candidate_list[j].date)):
                    LOG.debug("Found match with known day: %s" % candidate_list[j].date)
                    matches.append(candidate_list[j])
            
            # If there's one and only one match, combine the candidates
            if matches and len(matches)==1:
                LOG.debug("Combining %s and %s" % (candidate_list[i], matches[0]))
                matches[0].combine_candidate(candidate_list[i])
                del candidate_list[i]