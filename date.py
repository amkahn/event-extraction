#!/usr/bin/python

# Written by Andrea Kahn & Emily Silgard
# Last updated Aug. 15, 2014

'''
This module contains a Date class (a wrapper for python's datetime class that takes into account the possibility of fuzzy dates), as well as methods for the processing of date expressions in text.
'''

import logging
import re
from datetime import datetime

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.WARNING)


# Globals: Date Expressions
months={'January':'01','February':'02','March':'03','April':'04','May':'05','June':'06','July':'07','August':'08', 'September':'09','October':'10','November':'11','December':'12'}

month_abrvs={'Jan':'01','Feb':'02','Mar':'03','Apr':'04','Jun':'06','Jul':'07','Aug':'08','Sep':'09','Oct':'10','Nov':'11','Dec':'12'}

# fully named months, with years and possibly with days
str1 = '('+'|'.join(months.keys())+')[ ,]*(?:([\d]{1,2})(?:st|nd|rd|th)?)?[ ,\']+((?:(?:19)|(?:20)|\')[\d]{2})'

# common month abbreviations, with years and possibly days
str2 = '('+'|'.join(month_abrvs.keys())+')[ ,\.]*(?:([\d]{1,2})(?:st|nd|rd|th)?)?[ ,\']+((?:(?:19)|(?:20)|\')[\d]{2})'

# month/day/year
str3 = '([\d]{1,2})/([\d]{1,2})/((?:(?:19)|(?:20))?[\d]{2})'

# month-day-year
str4 = '([\d]{1,2})-([\d]{1,2})-((?:(?:19)|(?:20))?[\d]{2})'

# month/year or month-year
str5 = '([\d]{1,2})[/\-]((?:(?:19)|(?:20))[\d]{2})'

# "year in month" or "year in month abbreviation"
str6 = '((?:(?:19)|(?:20))[\d]{2}) in ('+'|'.join(month_abrvs.keys())+'|'.join(months.keys())+')'

# year/month/day 
str7 = '((?:(?:19)|(?:20))[\d]{2})/([\d]{1,2})/([\d]{1,2})'

# year-month-day
str8 = '((?:(?:19)|(?:20))[\d]{2})-([\d]{1,2})-([\d]{1,2})'

# just a year
str9 = '((?:(?:19)|(?:20))[\d]{2})'

# coordinated month and year combos
str10 = '('+'|'.join(month_abrvs.keys()+months.keys())+')[ ,\.]+and ('+'|'.join(month_abrvs.keys()+months.keys())+')[ ,\']+((?:(?:19)|(?:20))?[\d]{2})'

# coordinated year combos
str11 = '((?:(?:19)|(?:20))[\d]{2}) and ((?:(?:19)|(?:20))[\d]{2})'

date_regex = re.compile('(?:' + ')|(?:'.join([str1, str2, str3, str4, str5, str6, str7, str8, str9, str10, str11]) + ')')



class Date(object):
    '''
    A Date object has attributes 'dt' (a python datetime), 'day_known' (a boolean that is set to False if the day of the month is unspecified), and 'month_known' (a boolean that is set to False if the month is unspecified).
    NB: day_known and month_known are set to True by default; day_known must be specified in order for month_known to be specified.
    '''
    def __init__(self, dt, day_known=True, month_known=True):
        if day_known and (not month_known):
            LOG.warning("Initializing Date object with known day but unknown month")
    
        self.dt = dt
        self.day_known = day_known
        self.month_known = month_known

        
    def __repr__(self):
        return "Date: (%s, %s, %s)" % (self.dt, self.day_known, self.month_known)


    def __eq__(self, other):
        if type(other) != type(self):
            return False

        elif ((other.dt==self.dt) and (other.day_known==self.day_known) and (other.month_known==self.month_known)):
            return True

        else:
            return False

    
    def __ne__(self, other):
        return not __eq__(other)

    
    def __hash__(self):
        return hash(self.dt) + hash(self.day_known) + hash(self.month_known)


    def is_fuzzy_match(self, other):
        '''
        This method takes as input a second Date object and returns True if the input Date is a fuzzy match for this Date, else False.
        NB: The method returns True for exact matches as well.
        '''
        if type(other) != type(self):
            LOG.warning("Non-Date input cannot be a fuzzy match for Date object %s (input: %s)" % (self, str(other)))
            return False
        
        elif self==other:
            return True
        
        elif (other.dt==None) or (self.dt==None):
            return False
        
        elif (self.month_known==False) or (other.month_known==False):
            return (self.dt.year==other.dt.year)
        
        elif (self.day_known==False) or (other.day_known==False):
            return (self.dt.month==other.dt.month and self.dt.year==other.dt.year)
        
        else:
            return False


    def make_date_expression(self):
        '''
        This function can be thought of as the inverse of make_date(): It returns a string that, when fed as input to make_date(), will generate a Date object that is equivalent to this one.
        '''
        dt_str = str(self.dt).split()[0]
        
        if not self.month_known:
            dt_tokens = dt_str.split('-')
            return dt_tokens[0]
        elif not self.day_known:
            dt_tokens = dt_str.split('-')
            return dt_tokens[1]+'-'+dt_tokens[0]
        else:
            return dt_str



def extract_date(string, position):
    '''
    This method takes as input a string from which to extract a date and either 'first' or 'last' (specifying whether to return the first or last date found), and returns the first or last internal string that looks like a date.
    NB: This method returns a string corresponding to a date expression, not a Date object. The output can then be fed to make_date() to generate a Date object.
    '''
    if date_regex.search(string):
        if position=='first':
            date = min(date_regex.finditer(string), key=lambda x: x.start())
        if position=='last':
#           LOG.debug(string)
            date = max(date_regex.finditer(string), key=lambda x: x.start())
#           LOG.debug("Returning pre-window date %s" % date.group(0))
        return date.group(0)



def extract_dates_and_char_indices(string):
    '''
    This method takes as input a string from which to extract dates and returns a list of (Date, start_index, end_index) 3-tuples.
    '''
    to_return = []

    if date_regex.search(string):
        for match in date_regex.finditer(string):
            LOG.debug("Found date expression: %s" % match.group(0))
            match_dates = make_date(match.group(0))
            if match_dates:
                match_date = match_dates[0]
                match_start = match.start()
                match_end = match.end()
                to_return.append((match_date, match_start, match_end))
            else:
                LOG.warning("Tried unsuccessfully to make date from %s" % match.group(0))
                LOG.debug(string)
        
    return to_return



def make_date(string):
    '''
    This method takes a string as input and returns a list of representative Date objects. In most cases, this list is length 1, except for the case of coordinated years or coordinated month/year combos, in which the returned list is length 2.
    '''
    LOG.debug("Creating date from string %s" % string)
    
    mdy1 = re.compile(r'^('+'|'.join(months.keys())+')[ ,]*(?:([\d]{1,2})(?:st|nd|rd|th)?)?[ ,\']+((?:(?:19)|(?:20)|\')[\d]{2})$')
    mdy2 = re.compile(r'^('+'|'.join(month_abrvs.keys())+')[ ,\.]*(?:([\d]{1,2})(?:st|nd|rd|th)?)?[ ,\']+((?:(?:19)|(?:20)|\')[\d]{2})$')
    mdy3 = re.compile('^([\d]{1,2})([/\-])([\d]{1,2})\\2((?:(?:19)|(?:20))?[\d]{2})$')
    mdy4 = re.compile('^([\d]{1,2})[/\-]((?:(?:19)|(?:20))[\d]{2})$')
    mdy5 = re.compile('^((?:(?:19)|(?:20))[\d]{2}) in ('+'|'.join(month_abrvs.keys())+'|'.join(months.keys())+')$')
    mdy6 = re.compile('^((?:(?:19)|(?:20))[\d]{2})([/\-])([\d]{1,2})\\2([\d]{1,2})$')
    mdy7=re.compile('^((?:(?:19)|(?:20))[\d]{2})$')
    mdy8 = re.compile('^('+'|'.join(month_abrvs.keys()+months.keys())+')(?:[ ,\.\']+((?:(?:19)|(?:20))?[\d]{2}))?,? +and +('+'|'.join(month_abrvs.keys()+months.keys())+')[ ,\.\']+((?:(?:19)|(?:20))?[\d]{2})$')
    mdy9 = re.compile('^((?:(?:19)|(?:20))[\d]{2}) +and +((?:(?:19)|(?:20))[\d]{2})$')

    # Default is to assume years are 4 digits (always check and reset yr_string to 'y' if 2 digits)
    yr_string='Y'
    
    if mdy1.match(string):
        LOG.debug("Matched mdy1")
        if len(mdy1.match(string).group(3))==2:
            yr_string='y'
        
        # Start by looking for fully named months, with years and possibly with days  
        if mdy1.match(string).group(2):            
            dt = make_datetime_myd(mdy1.match(string).group(1),mdy1.match(string).group(3),mdy1.match(string).group(2),'%B,%'+yr_string+',%d')
            if dt:
                date = Date(dt)
                LOG.debug("Input was %s; matched mdy1; returning date %s" % (string, date))
                return [date]
            else:
                LOG.warning("Could not create Date object (text: %s)" % string)            

        # Back off to month and year (do nothing with month and two digits, which could be year or day)
        elif len(mdy1.match(string).group(3))==4:
            dt = make_datetime_my(mdy1.match(string).group(1),mdy1.match(string).group(3),'%B,%Y')
            if dt:
                date = Date(dt, False)
                LOG.debug("Input was %s; matched mdy1 with no day; returning date %s" % (string, date))
                return [date]
            else:
                LOG.warning("Could not create Date object (text: %s)" % string)
        
        # Deal with abbreviated years with apostrophes
        elif len(mdy1.match(string).group(3))==3:
            dt = make_datetime_my(mdy1.match(string).group(1),mdy1.match(string).group(3)[1:],'%B,%y')
            if dt:
                date = Date(dt, False)
                LOG.debug("Input was %s; matched mdy1 with no day; returning date %s" % (string, date))
                return [date]
            else:
                LOG.warning("Could not create Date object (text: %s)" % string)
        

    # Back off to common month abbreviations, with years and possibly days
    elif mdy2.match(string):
        LOG.debug("Matched mdy2")
        if len(mdy2.match(string).group(3))==2:
            yr_string='y'
            
        if mdy2.match(string).group(2):
            dt = make_datetime_myd(mdy2.match(string).group(1),mdy2.match(string).group(3),mdy2.match(string).group(2),'%b,%'+yr_string+',%d')
            date = Date(dt)
            LOG.debug("Input was %s; matched mdy2; returning date %s" % (string, date))
            return [date]

        # Back off to abbreviated month and year (do nothing with month and two digits, which could be year or day)
        elif len(mdy2.match(string).group(3))==4:
            dt = make_datetime_my(mdy2.match(string).group(1),mdy2.match(string).group(3),'%b,%Y')
            if dt:
                date = Date(dt, False)
                LOG.debug("Input was %s; matched mdy2 with abbreviated month; returning date %s" % (string, date))
                return [date]
            else:
                LOG.warning("Could not create Date object (text: %s)" % string)
        
        # Back off to abbreviated month and year abbreviated with apostrophe
        elif len(mdy2.match(string).group(3))==3:
            dt = make_datetime_my(mdy2.match(string).group(1),mdy2.match(string).group(3)[1:],'%b,%y')
            if dt:
                date = Date(dt, False)
                LOG.debug("Input was %s; matched mdy2 with abbreviated month; returning date %s" % (string, date))
                return [date]
            else:
                LOG.warning("Could not create Date object (text: %s)" % string)

    # Back off to month/day/year or month-day-year
    elif mdy3.match(string):
        LOG.debug("Matched mdy3")
        if len(mdy3.match(string).group(4))==2:
            yr_string='y'
        dt = make_datetime_myd(mdy3.match(string).group(1),mdy3.match(string).group(4),mdy3.match(string).group(3),'%m,%'+yr_string+',%d')
        if dt:
            date = Date(dt)
            LOG.debug("Input was %s; matched mdy3; returning date %s" % (string, date))
            return [date]
        else:
            LOG.warning("Could not create Date object (text: %s)" % string)

    # Back off to month/year or month-year
    elif mdy4.match(string):
        LOG.debug("Matched mdy4")     
        dt = make_datetime_my(mdy4.match(string).group(1),mdy4.match(string).group(2),'%m,%Y')
        if dt:
            date = Date(dt, False)
            LOG.debug("Input was %s; matched mdy4; returning date %s" % (string, date))
            return [date]
        else:
            LOG.warning("Could not create Date object (text: %s)" % string)
    
    # Back off to "year in month" or "year in month abbreviation"
    elif mdy5.match(string):
        LOG.debug("Matched mdy5")
        if mdy5.match(string).group(1) in months:
            dt = make_datetime_my(mdy5.match(string).group(2),mdy5.match(string).group(1),'%B,%Y')
        else:
            dt = make_datetime_my(mdy5.match(string).group(2),mdy5.match(string).group(1),'%b,%Y')
        if dt:
            date = Date(dt, False)
            LOG.debug("Input was %s; matched mdy5; returning date %s" % (string, date))
            return [date]
        else:
            LOG.warning("Could not create Date object (text: %s)" % string)

    # Back off to year/month/day or year-month-day
    elif mdy6.match(string):
        LOG.debug("Matched mdy6")
        dt = make_datetime_myd(mdy6.match(string).group(3),mdy6.match(string).group(1),mdy6.match(string).group(4),'%m,%'+yr_string+',%d')

        if dt:
            date = Date(dt)
            LOG.debug("Input was %s; matched mdy6; returning date %s" % (string, date))
            return [date]
        else:
            LOG.warning("Could not create Date object (text: %s)" % string)

    # Back off to just a year
    elif mdy7.match(string):
        LOG.debug("Matched mdy7")
        dt = make_datetime_y(mdy7.match(string).group(1),'%Y')

        if dt:
            date = Date(dt, False, False)
            LOG.debug("Input was %s; matched mdy7; returning date %s" % (string, date))
            return [date]
        else:
            LOG.warning("Could not create Date object (text: %s)" % string)

    # Look for coordinated month and year combos
    elif mdy8.match(string):
        LOG.debug("Matched mdy8")
        mdy8_match = mdy8.match(string)
        
        # If no year given for first month, use the second month's year
        if not mdy8_match.group(2):
            yr_group = mdy8_match.group(4)
        else:
            yr_group = mdy8_match.group(2)
            
        if len(yr_group)==2:
            yr_string='y'
        
        if mdy8_match.group(1) in months.keys():
            mo_string = 'B'
        else:
            mo_string = 'b'
        dt1 = make_datetime_my(mdy8_match.group(1), yr_group, '%'+mo_string+',%'+yr_string)
        
        if len(mdy8_match.group(4))==2:
            yr_string='y'
        else:
            yr_string='Y'

        if mdy8_match.group(3) in months.keys():
            mo_string = 'B'
        else:
            mo_string = 'b'
        dt2 = make_datetime_my(mdy8_match.group(3), mdy8_match.group(4), '%'+mo_string+',%'+yr_string)

        if dt1 and dt2:
            date1 = Date(dt1, False)
            date2 = Date(dt2, False)
            LOG.debug("Input was %s; matched mdy8; returning dates %s, %s" % (string, date1, date2))
            return [date1, date2]
        else:
            LOG.warning("Could not create Date object (text: %s)" % string)
    
    # Look for coordinated year combos
    elif mdy9.match(string):
        LOG.debug("Matched mdy9")
        mdy9_match = mdy9.match(string)

        dt1 = make_datetime_y(mdy9_match.group(1),'%Y')
        dt2 = make_datetime_y(mdy9_match.group(2),'%Y')

        if dt1 and dt2:    
            date1 = Date(dt1, False, False)
            date2 = Date(dt2, False, False)
            LOG.debug("Input was %s; matched mdy9; returning dates %s, %s" % (string, date1, date2))
            return [date1, date2]

        else:
            LOG.warning("Could not create Date object (text: %s)" % string)
    
    else:
        LOG.warning("Could not create Date object (text: %s)" % string)



# Helper methods for converting strings to datetime objects
# NB: Unknown days or months will default to '1'
# See https://docs.python.org/2/library/datetime.html for documentation on the format_strings

def make_datetime_y(year,format_string):
    return datetime.strptime(year,format_string)


def make_datetime_my(month,year,format_string):
    if len(month)==1:month='0'+month
    try:
        return datetime.strptime(month+','+year,format_string)
    except ValueError:
        LOG.warning("Input was month %s, year %s; cannot make date" % (month, year))


def make_datetime_myd(month,year,day,format_string):
    if len(month)==1:
        month='0'+month
    if len(day)==1:
        day='0'+day
    try:
        return datetime.strptime(month+','+year+','+day,format_string)
    except ValueError:
           LOG.warning("ValueError: month %s, year %s, day %s, format_string %s" % (month, year, day, format_string))
           return None