Author: Andrea Kahn
amkahn@uw.edu
Aug. 29, 2014


Motivation:
To extract the most likely dates of clinical events using pattern matching and keyword sets. A ‘verbose’ output option returns supporting text snippets along with dates and confidence scores, allowing the user to review the snippets and make the final decision about which dates are most likely correct. An evaluation script allows the user to assess the effectiveness of their chosen keyword set on labeled data and adjust the keyword set accordingly.


Files:
extract_events.py: The module for event date extraction. It can be run as an executable from the command line, or it can be imported and its extract_events() and naive_extract_events() methods can be used directly.
eval_output.py: The module for output evaluation. It can be run as an executable from the command line, or it can be imported and its print_results(), print_output_comparison(), and print_output_not_in_top_n() methods can be used directly.
date.py: A module for the processing of date expressions in text, including the Date class definition (imported and used by extract_events.py and eval_output.py).
date_candidate.py: A module for the scoring, collapsing, and ranking of candidate dates, as well as the DateCandidate class definition (imported and used by extract_events.py and eval_output.py).


Input: extract_events.py:
1) A path to a file containing patients' clinic notes, each line having the format: MRN [tab] date [tab] description [tab] note (one note per line; date must be in format YYYY-MM-DD, YYYY-MM, or YYYY; text blob cannot contain tabs)
2) A path to the file containing keywords to search on, each line having the format: keyword [tab] position ([tab] window size), where position is PRE-DATE or POST-DATE and the parenthesized content is optional (default window size = 100) (NB: casing of keywords is ignored)
3) Optionally, a float corresponding to the minimum score a date candidate must have in order to be output (default = 0.0)
4) Optionally, an int corresponding to the minimum number of dates to be output, regardless of whether they all have the minimum score (NB: if the number of date candidates extracted is lower than this int, only the number of date candidates extracted will be output) (default = 0)

Command line usage: ./extract_events.py <notes-file> <data-file>
OR
./extract_events.py <notes-file> <data-file> <filter>
OR
./extract_events.py <notes-file> <data-file> <filter> <n>

Output: extract_events.py:
The program extracts dates correlated with the keywords from the patients' clinic notes and prints to standard out lines in the following format (one line per patient):
MRN [tab] date1 [tab] score1 [tab] date2 [tab] score2 ... 

...where MRNs are sorted alphabetically, and dates for a particular patient appear in descending order by score.

To switch to verbose output (lists of supporting snippets are printed after scores), comment line 61 and uncomment line 62.


Module usage: extract_events.py:
Alternatively, the module can be imported and the extract_events() and naive_extract_events() methods can be used directly.

extract_events() takes as input a list of ClinicNote objects, a list of Keyword objects, an optional minimum confidence score (float; default = 0.0), and an optional int 'n' referring to the minimum number of candidate dates to be returned (default = 0), and returns a list of DateCandidate objects corresponding with date expressions that the system has identified in the patient's clinic notes based on Keyword objects.

naive_extract_events() takes as input a list of ClinicNote objects and returns a list of DateCandidate objects corresponding with ALL date expressions that the system has identified in the patient's clinic notes. (Not called in main method, it is intended to be used to establish a recall ceiling for evaluation -- i.e., to see how many of the gold dates actually appear in the notes at all.)

Keyword and ClinicNote class definitions are contained within the module extract_events.py.


Input: eval_output.py:
1) A path to the output file, where each line corresponds with a patient and takes the format: MRN [tab] date1 [tab] score1 [tab] date2 [tab] score2 ... (non-verbose format of output from extract_events.py)
2) A path to the gold data file, where each line corresponds with a patient and takes the format: MRN[tab]gold_date_1[tab]gold_date_2 ...

Command line usage:./eval_output.py <output-filename> <gold-data-file>

Output: eval_output.py:
The program calculates various evaluation metrics and prints them to standard out.
To print or not print evaluation metrics (including recall, precision, F1, etc.), uncomment or comment line 40.
To print or not print a side-by-side comparison of gold dates and system-output dates, uncomment or comment line 41.
To print or not print a side-by-side comparison of gold dates and system-output dates for patients for whom a gold date does not appear in the top n dates output by the system, uncomment or comment line 42.

Module usage: eval_output.py:
Alternatively, the module can be imported and the print_results(), print_output_comparison(), and print_output_not_in_top_n() methods can be used directly.

print_results() takes as input a hash of MRN mapped to gold dates (Date objects) and a hash of MRNs mapped to lists of DateCandidate objects returned by the system. It then prints various evaluation metrics to standard out.

print_output_comparison() takes as input a hash of MRN mapped to gold dates (Date objects), a hash of MRNs mapped to lists of DateCandidate objects returned by the system, an int n, and an optional measure (string 'strict' or 'lenient'; default is 'strict'). It then prints to standard out, for each patient for whom A correct date does not appear in the top n dates returned: MRN ground_truth extracted_by_sys (where extracted_by_sys is all dates returned, including the top n).

print_output_not_in_top_n() takes as input a hash of MRN mapped to gold dates (Date objects), a hash of MRNs mapped to lists of DateCandidate objects returned by the system, an int n, and an optional measure (string 'strict' or 'lenient'; default is 'strict'). It then prints to standard out, for each patient for whom A correct date does not appear in the top n dates returned: MRN ground_truth extracted_by_sys (where extracted_by_sys is all dates returned, including the top n).


Specifications:
This program was developed in python 2.7.5.
It uses the following python modules: sys, logging, re, datetime.


Logging:
Set to WARNING level. To change to DEBUG, edit the following lines:
extract_events.py: line 29
eval_output.py: line 19
date.py: line 15
date_candidate.py: line 12