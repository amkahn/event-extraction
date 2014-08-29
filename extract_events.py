#!/usr/bin/python

# Written by Andrea Kahn
# Last updated Aug. 29, 2014


'''
This script takes as input:
1) A path to a file containing patients' clinic notes, each line having the format: MRN [tab] date [tab] description [tab] note (one note per line; date must be in format YYYY-MM-DD, YYYY-MM, or YYYY)
2) A path to the file containing keywords to search on, each line having the format: keyword [tab] position ([tab] window size), where position is PRE-DATE or POST-DATE and the parenthesized content is optional (default window size = 100) (NB: casing of keywords is ignored)
3) Optionally, a float corresponding to the minimum score a date candidate must have in order to be output (default = 0.0)
4) Optionally, an int corresponding to the minimum number of dates to be output, regardless of whether they all have the minimum score (NB: if the number of date candidates extracted is lower than this int, only the number of date candidates extracted will be output) (default = 0)

It then extracts dates correlated with the keywords from the patients' clinic notes and prints to standard out lines in the following format (one line per patient):
MRN [tab] date1 [tab] score1 [tab] date2 [tab] score2 ... 

...where MRNs are sorted alphabetically, and dates for a particular patient appear in descending order by score.

To switch to verbose output (lists of supporting snippets are printed after scores), comment line 61 and uncomment line 62.
'''


from sys import argv
import logging
from date import *
from date_candidate import *

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.WARNING)


def main():
    logging.basicConfig()

    notes_filename = argv[1]
    keywords_filename = argv[2]
    if len(argv) > 3:
        filter = argv[3]
        if len(argv) > 4:
            n = argv[4]
        else:
            n = 0
    else:
        filter = 0.0
        n = 0
    
    notes_file = open(notes_filename)
    notes_dict = get_notes_dict(notes_file)
    notes_file.close()
    LOG.debug("Here is the notes dictionary: %s" % notes_dict)

    keywords_file = open(keywords_filename)
    keywords_list = get_keywords_list(keywords_file)
    keywords_file.close()
    LOG.debug("Here is the keywords list: %s" % keywords_list)
    
    extracted = {}
    for MRN in notes_dict:
        extracted[MRN] = extract_events(notes_dict[MRN], keywords_list, filter, n)

    print_output(extracted)
#   print_output(extracted, True)


class ClinicNote(object):
    '''
    A ClinicNote has attributes 'date' (a Date object corresponding to the document creation date), 'desc' (a string corresponding to the description of the clinic note), and 'text' (a text blob corresponding to the contents of the note).
    '''
    def __init__(self, date, desc, text):
        self.date = date
        self.desc = desc
        self.text = text
    
    def __repr__(self):
        return "date: %s; desc: %s" % (self.date, self.desc)
#       return "date: %s; desc: %s; text: %s" % (self.date, self.desc, self.text)



class Keyword(object):
    '''
    A Keyword has 'text' (the keyword itself), 'position' (the string 'PRE-DATE' or 'POST-DATE'), an int 'window' (the number of characters before or after the keyword in which to look for a date). The last attribute, if not passed into the __init__ method, defaults to 100.
    '''
    def __init__(self, text, position, window=100):
        if position not in ['PRE-DATE', 'POST-DATE']:
            LOG.warning("Bad position value %s; setting position to None)" % str(position))
        
        self.text = text
        self.position = position
        self.window = int(window)
    
    def __repr__(self):
        return "(%s, %s, %s)" % (self.text, self.position, str(self.window))



def get_notes_dict(file):
    '''
    This method takes as input an open file object and returns a dictionary of MRNs mapped to lists of ClinicNote objects corresponding to the clinic notes for that patient.
    '''
    notes_dict = {}
    
    for line in file:
        line_elements = line.strip().split('\t')
        if len(line_elements) not in [3, 4]:
            LOG.warning("Bad notes file line format; skipping: %s" % line)
        else:
            if len(line_elements) == 3:
                note = ClinicNote(line_elements[1], line_elements[2], '')
            else:
                note = ClinicNote(line_elements[1], line_elements[2], line_elements[3])
            if notes_dict.get(line_elements[0]):
                notes_dict[line_elements[0]].append(note)
            else:
                notes_dict[line_elements[0]] = [note]
            
    return notes_dict


def get_keywords_list(file):
    '''
    This method takes as input an open file object and returns a list of Keyword objects.
    '''
    keywords = []
    
    for line in file:
        line_elements = line.strip().split('\t')
        if len(line_elements) not in [2, 3]:
            LOG.warning("Bad keywords file line format; skipping: %s" % line)
        else:
            text = line_elements[0]
            position = line_elements[1]
            if len(line_elements) == 3:
                keyword = Keyword(text, position, line_elements[2])
            else:
                keyword = Keyword(text, position)
            keywords.append(keyword)
        
    return keywords


def extract_events(notes_list, keywords_list, filter=0.0, n=0):
    '''
    This function takes as input a list of ClinicNote objects, a list of Keyword objects, an optional minimum confidence score (float; default = 0.0), and an optional int 'n' referring to the minimum number of candidate dates to be returned (default = 0), and returns a list of DateCandidate objects corresponding with date expressions that the system has identified in the patient's clinic notes based on Keyword objects.
    '''
    extracted = get_date_candidates(notes_list, keywords_list)
    rerank_candidates(extracted, filter, n)
    return extracted
    

def naive_extract_events(notes):
    '''
    This function takes as input a list of ClinicNote objects and returns a list of DateCandidate objects corresponding with ALL date expressions that the system has identified in the patient's clinic notes. (Not called in current code, it is intended to be used to establish a recall ceiling for evaluation -- i.e., to see how many of the gold dates actually appear in the notes at all.)
    '''
    candidates = []

    for note in notes:
        dates = [x[0] for x in extract_dates_and_char_indices(note.text)]

        for d in dates:
            date_candidate = DateCandidate(d, [note.text])
            candidates.append(date_candidate)
    
    rerank_candidates(candidates)
    return candidates


def get_date_candidates(notes, keywords):
    '''
    This method takes as input a list of ClinicNote objects and a list of Keyword objects. It then returns a list of DateCandidate objects representing dates that appear in the clinic notes correlated with the input keywords.
    '''
    candidates = []
    pre_date_keywords = filter(lambda x: x.position=='PRE-DATE', keywords)
    post_date_keywords = filter(lambda x: x.position=='POST-DATE', keywords)
    LOG.debug("Here are the pre-date keywords: %s" % pre_date_keywords)
    LOG.debug("Here are the post-date keywords: %s" % post_date_keywords)
    
    # Store the window sizes in a dictionary that maps (keyword text, position) tuples to window sizes
    window_sizes = {}
    for keyword in keywords:
        window_sizes[(keyword.text.lower(), keyword.position)] = keyword.window
    
    if pre_date_keywords:
#       pre_date_regex = re.compile('|'.join(['['+keyword[0].upper()+keyword[0]+']'+keyword[1:] for keyword in pre_date_keywords]))
        pre_date_keywords = map(lambda w: ''.join(map(lambda x: '[' + x.upper() + x + ']', w.text)), pre_date_keywords)
        pre_date_regex = re.compile('|'.join(pre_date_keywords))

    if post_date_keywords:
#       post_date_regex = re.compile('|'.join(['['+keyword[0].upper()+keyword[0]+']'+keyword[1:] for keyword in post_date_keywords]))
        post_date_keywords = map(lambda w: ''.join(map(lambda x: '[' + x.upper() + x + ']', w.text)), post_date_keywords)
        post_date_regex = re.compile('|'.join(post_date_keywords))
    
    for note in notes:
        
        if pre_date_keywords:
            pre_date_matches = pre_date_regex.finditer(note.text)
            for match in pre_date_matches:
                LOG.debug("Found pre-date keyword match: %s" % match.group(0))
                window_size = window_sizes[(match.group(0).lower(), 'PRE-DATE')]
                
                # Set the window beginning at the start of the match to pre_date_window_size characters or all remaining characters, whichever is less
                window = note.text[match.start(0):(match.end(0)+window_size)]
        
                # Look for first date in window -- do not pass a period or the end of the text
                snippet = re.split('[.]|[a-z],|dmitted|:.*:', window)[0]
                LOG.debug("Looking for date in: %s" % snippet)

                event_date_str = extract_date(snippet, 'first')
                LOG.debug("Extracted: %s" % event_date_str)
                if event_date_str:
                    LOG.debug("Found date expression: %s" % event_date_str)
                    event_dates = make_date(event_date_str)
                
                    # FIXME: Consider alternatives that keep coordinated dates together (or throw them out entirely)
                    if event_dates:
                        for event_date in event_dates:
                            date_candidate = DateCandidate(event_date, [snippet])
                            candidates.append(date_candidate)
            
            else:
                LOG.debug("No date expression found")
        
        if post_date_keywords:      
            LOG.debug("Looking for postdate matches")
            post_date_matches = post_date_regex.finditer(note.text)
            for match in post_date_matches:
                LOG.debug("Found post-date keyword match: %s" % match.group(0))
                window_size = window_sizes[(match.group(0).lower(), 'POST-DATE')]
                
                # Set the window to include the event expression and the prewindow_size characters before the event expression or all preceding characters, whichever is less
                window = note.text[(match.start(0)-window_size):match.end(0)]
        
                # Look for the last date in the window -- do not pass a period
                snippet = re.split('[.]|[a-z],|<%END%>|ischarge|dmitted.{20}', window)[-1]
                LOG.debug("Looking for date in: %s" % snippet)
            
                event_date_str = extract_date(snippet, 'last')
                LOG.debug("Extracted: %s" % event_date_str)        
                if event_date_str:
                    LOG.debug("Found date expression: %s" % event_date_str)
                    event_dates = make_date(event_date_str)
                                          
                    if event_dates:
                        for event_date in event_dates:
                            date_candidate = DateCandidate(event_date, [snippet])
                            candidates.append(date_candidate)

    return candidates


def print_output(output_dict, verbose=False):
    '''
    This method takes as input a hash of MRNs mapped to lists of DateCandidate objects and a boolean True or False specifying whether or not supporting snippets should be printed (default: False), and prints to standard out lines in the following format: MRN [tab] date1 [tab] score1 [tab] (snippets_list1 [tab]) date2 [tab] score2 (snippets_list2 [tab])... , where dates appear in descending order by score.
    '''
    for MRN in output_dict:
        sorted_candidates = sorted(output_dict[MRN], key=lambda candidate: candidate.score, reverse=True)
        if verbose:
            print MRN+'\t'+'\t'.join([c.date.make_date_expression()+'\t'+str(c.score)+'\t'+str(c.snippets) for c in sorted_candidates])
        else:
            print MRN+'\t'+'\t'.join([c.date.make_date_expression()+'\t'+str(c.score) for c in sorted_candidates])


if __name__=='__main__':
    main()