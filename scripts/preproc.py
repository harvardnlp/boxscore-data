import re
import json, sys, os, codecs
from nltk import word_tokenize

num_patt = re.compile('([+-]?\d+(?:\.\d+)?)')

def to_int(matchobj):
    num = int(round(float(matchobj.group(0)),0)) # rounds to nearest integer
    return str(num)


# functions below do the following:
# - tokenizes and separates hyphens from summaries
# - maps everything to an integer; pcts are in [0, 100]

def prep_tokes(thing):
    # remove all newline stuff
    summ = thing['summary'].replace(u'\xa0', ' ')
    summ = summ.replace('\\n', ' ').replace('\r', ' ')
    summ = re.sub("<[^>]*>", " ", summ)
    # replace all numbers with rounded integers
    summ = num_patt.sub(to_int, summ)
    tokes = word_tokenize(summ)
    # replace hyphens
    newtokes = []
    [newtokes.append(toke) if toke[0].isupper() or '-' not in toke
      else newtokes.extend(toke.replace('-', " - ").split()) for toke in tokes]
    thing['summary'] = newtokes

def prep_nums(thing):
    # do box scores
    for k, d in thing['box_score'].iteritems():
        if "PCT" in k:
            for idx, pct in d.iteritems():
                if pct is not None:
                    d[idx] = str(int(round(float(pct)*100, 0)))
                else:
                    d[idx] = "N/A"
        elif k == "MIN":
            for idx, time in d.iteritems():
                if time is not None:
                    mins, seconds = None, None
                    try:
                        mins, seconds = time.split(':') # these are actually probably minutes and seconds
                    except AttributeError as ex: # sometimes these are integers i guess
                        mins, seconds = time, 0
                    frac_mins = float(mins) + float(seconds)/60
                    d[idx] = str(int(round(frac_mins, 0)))
                else:
                    d[idx] = "N/A"
        else: # everything else assumed to be integral
            for idx, num in d.iteritems():
                # see if we can make it a number
                if num is not None and num != "":
                    try:
                        fnum = float(num)
                        d[idx] = str(int(round(fnum, 0)))
                    except ValueError:
                        pass
                else:
                    d[idx] = "N/A"

    # do line scores
    linekeys = ['home_line', 'vis_line']
    for lk in linekeys:
        for k in thing[lk].keys():
            v = thing[lk][k]
            if "PCT" in k and v is not None:
                thing[lk][k] = str(int(round(float(v)*100, 0)))
            elif k == "TEAM_WINS_LOSSES" and v is not None:
                wins, losses = v.split('-')
                thing[lk]['WINS'] = wins
                thing[lk]['LOSSES'] = losses
                del thing[lk][k]
            elif v is not None:
                try:
                    fnum = float(v)
                    thing[lk][k] = str(int(round(fnum, 0)))
                except ValueError:
                    pass


def add_player_names(thing):
    # will leave off any third name nonsense
    thing['box_score']['FIRST_NAME'] = {}
    thing['box_score']['SECOND_NAME'] = {}
    for k, v in thing['box_score']['PLAYER_NAME'].iteritems():
        names = v.split()
        thing['box_score']['FIRST_NAME'][k] = names[0]
        thing['box_score']['SECOND_NAME'][k] = names[1] if len(names) > 1 else "N/A"


def add_team_names(thing):
    thing['home_line']['CITY'] = thing['home_city']
    thing['home_line']['NAME'] = thing['home_name']
    thing['vis_line']['CITY'] = thing['vis_city']
    thing['vis_line']['NAME'] = thing['vis_name']


def prep_roto():
    with codecs.open("rotoaligned.json", "r", "utf-8") as f:
        data = json.load(f)

    for thing in data:
        prep_nums(thing)
        prep_tokes(thing)
        add_player_names(thing)
        add_team_names(thing)
        # rename home and away linescore keys so they don't conflict
        linekeys = ['home_line', 'vis_line']
        for lk in linekeys:
            for k in thing[lk].keys():
                v = thing[lk][k]
                thing[lk]["TEAM-" + k] = v
                del thing[lk][k]

    # read in keys in each (random) split, and split dataset
    with codecs.open("roto_split_keys.txt", "r", "utf-8") as f:
        lines = f.readlines()
        ntrain, nval, ntest = lines[0].split()
        ntrain, nval, ntest = int(ntrain), int(nval), int(ntest)
        lines = lines[1:]
        trkeys = set([thing.strip() for thing in lines[:ntrain]])
        valkeys = set([thing.strip() for thing in lines[ntrain:ntrain+nval]])
        testkeys = set([thing.strip() for thing in lines[ntrain+nval:]])
        train, val, test = [], [], []
        for thing in data:
            # get the key
            key = (thing["day"] + "-" + thing["home_name"] + "-"
                    + thing["vis_name"] + "-" + "".join(thing["summary"][:5]))
            if key in testkeys:
                test.append(thing)
            elif key in valkeys:
                val.append(thing)
            else:
                train.append(thing)

    # finally write everything
    try:
        os.makedirs("rotowire")
    except OSError as ex:
        if "File exists" in ex:
            print ex
        else:
            raise ex
    with codecs.open("rotowire/train.json", "w+", "utf-8") as f:
        json.dump(train, f)
    with codecs.open("rotowire/valid.json", "w+", "utf-8") as f:
        json.dump(val, f)
    with codecs.open("rotowire/test.json", "w+", "utf-8") as f:
        json.dump(test, f)


def paragraph_stuff(thing, thresh=2):
    pars = thing["summary"].split("\n\n") # assume more than one newline is a new par
    newpars = []
    discarded = 0 # just for threshold stuff
    for par in pars:
        if len(par) > 0 and not par.isspace():
            if "twitter.com" in par or "(@" in par or "(Video" in par:
                continue
            if "Final" in par and "1" in par and "2" in par and "3" in par and "4" in par: # stupid FINAL 1 2 3 4 thing
                break
            tokes = par.replace('-', ' - ').replace('(', ' ( ').replace(')', ' ) ').split()
            num_nums = sum((1 for toke in tokes if toke.isdigit() or toke in number_words))
            if num_nums >= thresh:
                newpars.append(par)
            else:
                discarded += 1
    thing["summary"] = " *NEWPARAGRAPH* ".join(newpars)
    return discarded



def prep_sb(min_summ_len=35):
    data = []
    with codecs.open("sbaligned.json", "r", "utf-8") as f:
        for line in f:
            obj = json.loads(line.strip())
            if obj is not None:
                data.append(obj)

    discarded = 0

    for thing in data:
        discarded += paragraph_stuff(thing)
        prep_nums(thing)
        prep_tokes(thing)
        add_player_names(thing)
        add_team_names(thing)
        # rename home and away linescore keys so they don't conflict
        linekeys = ['home_line', 'vis_line']
        for lk in linekeys:
            for k in thing[lk].keys():
                v = thing[lk][k]
                thing[lk]["TEAM-" + k] = v
                del thing[lk][k]

    print "discarded", discarded

    # get rid of stuff w/ empty or too short summaries
    data = [thing for thing in data if len(thing["summary"]) >= min_summ_len]

    # read in keys in each (random) split, and split dataset
    with codecs.open("sb_split_keys.txt", "r", "utf-8") as f:
        lines = f.readlines()
        ntrain, nval, ntest = lines[0].split()
        ntrain, nval, ntest = int(ntrain), int(nval), int(ntest)
        lines = lines[1:]
        trkeys = set([thing.strip() for thing in lines[:ntrain]])
        valkeys = set([thing.strip() for thing in lines[ntrain:ntrain+nval]])
        testkeys = set([thing.strip() for thing in lines[ntrain+nval:]])
        train, val, test = [], [], []
        for thing in data:
            # get the key
            key = (thing["day"] + "-" + thing["home_name"] + "-"
                    + thing["vis_name"] + "-" + "".join(thing["summary"][:10]))
            if key in testkeys:
                test.append(thing)
            elif key in valkeys:
                val.append(thing)
            else:
                train.append(thing)

    # finally write everything
    try:
        os.makedirs("sbnation")
    except OSError as ex:
        if "File exists" in ex:
            print ex
        else:
            raise ex
    with codecs.open("sbnation/train.json", "w+", "utf-8") as f:
        json.dump(train, f)
    with codecs.open("sbnation/valid.json", "w+", "utf-8") as f:
        json.dump(val, f)
    with codecs.open("sbnation/test.json", "w+", "utf-8") as f:
        json.dump(test, f)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "sbnation":
        prep_sb()
    else:
        prep_roto()
