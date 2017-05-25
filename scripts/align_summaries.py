import re, datetime
import json, sys, os, codecs
import nba_py
import nba_py.game
import numpy as np
from HTMLParser import HTMLParser
h = HTMLParser()

months = {"January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
          "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12}

def game_metadata_from_html(html):
    dates = []
    for match in re.finditer('<div class="time-big-light">Final(.*)</div>', html):
        pieces = match.groups()[0].split('&nbsp;')[-3:]
        datestr = "%s_%s_%s" % (pieces[2], str(months[pieces[0]]), str(pieces[1].strip(',')))
        dates.append(datestr)

    games = []
    i = 0
    for match in re.finditer('href=.*>(.*)<span .*>at</span>(.*)</a>', html):
        assert len(match.groups()) == 2
        away = match.groups()[0].split()[:-1]
        home = match.groups()[1].split()[1:]
        if i < len(dates):
            games.append((match.start(), away, home, dates[i], []))
        else:
            print >> sys.stderr, "found more games than dates; using last date..."
            games.append((match.start(), away, home, dates[-1], []))
        i += 1

    return games


# this tries to map each summary in the nba/ directory to the date given on the webpage for the game
def write_intermediate_json(direc):
    all_games = {}
    for fi in os.listdir(direc):
        daystr = fi[6:]
        if daystr == "01_01_14": # this day has like duplicates of everything for some weird reason
            continue
        html = None
        with codecs.open(os.path.join(direc, fi), "r", "utf-8") as f:
            try:
                html = f.read()
            except UnicodeDecodeError:
                with open(os.path.join(direc, fi)) as f:
                   html = f.read()
                   html = unicode(html, errors='ignore')
            # first get all the games for this day
            games = game_metadata_from_html(html)
            if len(games) > 0:
                for a in re.finditer('<div class="light-content" style="margin-bottom:20px;">([^<]*)</div>', html):
                    start = a.start()
                    # find closest game title (in terms of text position)
                    best = -1 # note, trickily selects last one by default
                    for i in xrange(1, len(games)):
                        if games[i][0] > start:
                            best = i-1
                            break
                    summary = h.unescape(a.group(1)).replace("<br />", " ")
                    games[best][4].append(summary)
                for i in xrange(len(games)):
                    if games[i][3] not in all_games:
                        all_games[games[i][3]] = []
                    all_games[games[i][3]].append({'home': " ".join(games[i][1]),
                                                   'away': " ".join(games[i][2]),
                                                   'summaries': games[i][4]})
    with codecs.open("temp.json", "w+", "utf-8") as f:
        json.dump(all_games, f)

def add_to_data(day, linescores, awayrow, texts, data):
    # N.B. in linescores it's away then home
    awayid = linescores.iloc[awayrow][3]
    homeid = linescores.iloc[awayrow+1][3]
    gameid = linescores.iloc[awayrow][2]
    # N.B. in boxscores it's home then away. go figure.
    bs = nba_py.game.Boxscore(gameid)
    home_name, home_city = bs.team_stats().iloc[0]['TEAM_NAME'], bs.team_stats().iloc[0]['TEAM_CITY']
    away_name, away_city = bs.team_stats().iloc[1]['TEAM_NAME'], bs.team_stats().iloc[1]['TEAM_CITY']
    homeline = linescores.iloc[awayrow+1]
    awayline = linescores.iloc[awayrow]
    stats = bs.player_stats()
    if data is not None:
        for text in texts:
            data.append({"day" : day.strftime("%0m_%0d_%y"),
                         "summary": text,
                         "home_name": home_name,
                         "vis_name": away_name,
                         "home_city": home_city,
                         "vis_city": away_city,
                         "home_line":  json.loads(homeline[["TEAM_WINS_LOSSES", "PTS_QTR1", "PTS_QTR2", "PTS_QTR3", "PTS_QTR4", "PTS", "FG_PCT", "FT_PCT", "FG3_PCT", "AST", "REB", "TOV"]].to_json()),
                         "vis_line":   json.loads(awayline[["TEAM_WINS_LOSSES", "PTS_QTR1", "PTS_QTR2", "PTS_QTR3", "PTS_QTR4", "PTS", "FG_PCT", "FT_PCT", "FG3_PCT", "AST", "REB", "TOV"]].to_json()),
                         "box_score" : json.loads(stats[["TEAM_CITY", "START_POSITION", "PLAYER_NAME", "MIN", "FGM", "FGA", "FG_PCT", "FG3M", "FG3A", "FG3_PCT", "FTM", "FTA", "FT_PCT", "OREB", "DREB", "REB", "AST", "STL", "BLK", "TO", "PF", "PTS"]].to_json())
                     })
    else:
        return {"day" : day.strftime("%0m_%0d_%y"),
                     "summary": texts[0],
                     "home_name": home_name,
                     "vis_name": away_name,
                     "home_city": home_city,
                     "vis_city": away_city,
                     "home_line":  json.loads(homeline[["TEAM_WINS_LOSSES", "PTS_QTR1", "PTS_QTR2", "PTS_QTR3", "PTS_QTR4", "PTS", "FG_PCT", "FT_PCT", "FG3_PCT", "AST", "REB", "TOV"]].to_json()),
                     "vis_line":   json.loads(awayline[["TEAM_WINS_LOSSES", "PTS_QTR1", "PTS_QTR2", "PTS_QTR3", "PTS_QTR4", "PTS", "FG_PCT", "FT_PCT", "FG3_PCT", "AST", "REB", "TOV"]].to_json()),
                     "box_score" : json.loads(stats[["TEAM_CITY", "START_POSITION", "PLAYER_NAME", "MIN", "FGM", "FGA", "FG_PCT", "FG3M", "FG3A", "FG3_PCT", "FTM", "FTA", "FT_PCT", "OREB", "DREB", "REB", "AST", "STL", "BLK", "TO", "PF", "PTS"]].to_json())
                 }

def align_rotowire():
    with codecs.open("temp.json", "r", "utf-8") as f:
        rotodat = json.load(f)

    data = []

    delts = [datetime.timedelta(days=0), datetime.timedelta(days=-1),
        datetime.timedelta(days=1), datetime.timedelta(days=-2), datetime.timedelta(days=2)]

    for daykey, dayvals in rotodat.iteritems():
        date_pieces = daykey.split('_')
        day = datetime.date(int(date_pieces[0]), int(date_pieces[1]), int(date_pieces[2]))
        for thing in dayvals:
            foundgame = False
            rulhome1 = thing["home"].split()[0]
            if rulhome1 == "Los" and "Clippers" in thing["home"]:
                rulhome1 = "LA"
            rulaway1 = thing["away"].split()[0]
            if rulaway1 == "Los" and "Clippers" in thing["away"]:
                rulaway1 = "LA"
            for delt in delts:
                newday = day + delt
                scoreboard = nba_py.Scoreboard(month=newday.month, day=newday.day, year=newday.year)
                linescores = scoreboard.line_score()
                for i in xrange(0, len(linescores), 2):
                    awaycity1 = linescores.iloc[i][5].split()[0]
                    homecity1 = linescores.iloc[i+1][5].split()[0]
                    #print "got", homecity1, awaycity1
                    if rulhome1 == homecity1 and rulaway1 == awaycity1 or rulhome1 == awaycity1 and rulaway1 == homecity1: # found it
                        add_to_data(newday, linescores, i, thing["summaries"], data)
                        foundgame = True
                        break
                if foundgame:
                    break

            if not foundgame:
                print >> sys.stderr, "couldn't find", daykey, rulhome1, rulaway1

    with codecs.open("rotoaligned.json", "w+", "utf-8") as f:
        json.dump(data, f)



teams = ['Atlanta Hawks', 'Boston Celtics', 'Brooklyn Nets', 'Charlotte Hornets',
 'Chicago Bulls', 'Cleveland Cavaliers', 'Detroit Pistons', 'Indiana Pacers',
 'Miami Heat', 'Milwaukee Bucks', 'New York Knicks', 'Orlando Magic',
 'Philadelphia 76ers', 'Toronto Raptors', 'Washington Wizards', 'Dallas Mavericks',
 'Denver Nuggets', 'Golden State Warriors', 'Houston Rockets', 'Los Angeles Clippers',
 'Los Angeles Lakers', 'Memphis Grizzlies', 'Minnesota Timberwolves', 'New Orleans Pelicans',
 'Oklahoma City Thunder', 'Phoenix Suns', 'Portland Trail Blazers', 'Sacramento Kings',
 'San Antonio Spurs', 'Utah Jazz']
two_word_cities = ['New York', 'Golden State', 'Los Angeles', 'New Orleans', 'Oklahoma City', 'San Antonio']
two_word_teams = ['Trail Blazers']

ec = {} # equivalence classes
for team in teams:
    pieces = team.split()
    if len(pieces) == 2:
        ec[team] = [pieces[0], pieces[1]]
    elif pieces[0] == "Portland": # only 2-word team
        ec[team] = [pieces[0], " ".join(pieces[1:])]
    else: # must be a 2-word City
        ec[team] = [" ".join(pieces[:2]), pieces[2]]
# add nicknames
ec["Cleveland Cavaliers"].append("Cavs")
ec["Philadelphia 76ers"].append("Sixers")
ec["Dallas Mavericks"].append("Mavs")
ec["Minnesota Timberwolves"].append("Wolves")
ec["Portland Trail Blazers"].append("Blazers")

def matches(team1, team2, homecity, awaycity):
    if homecity in team1 and awaycity in team2:
        return True
    if homecity in team2 and awaycity in team1:
        return True
    # one is LA
    if "Los" in team1 and "LA" in homecity and awaycity in team2:
        return True
    if "Los" in team1 and "LA" in awaycity and homecity in team2:
        return True
    if "Los" in team2 and "LA" in homecity and awaycity in team1:
        return True
    if "Los" in team2 and "LA" in awaycity and homecity in team1:
        return True
    # both are LA
    if "Los" in team1 and "LA" in homecity and "Los" in team2 and "LA" in awaycity:
        return True
    if "Los" in team2 and "LA" in homecity and "Los" in team1 and "LA" in awaycity:
        return True
    return False

def align_sbnation():
    num_skipped = 0
    num_weird = 0
    delts = [datetime.timedelta(days=0), datetime.timedelta(days=-1),
       datetime.timedelta(days=1), datetime.timedelta(days=-2), datetime.timedelta(days=2)]
    with codecs.open("sbaligned.json", "w+", "utf-8") as g:
        with codecs.open("sbnba.json", "r", "utf-8") as f:
            for ii, line in enumerate(f):
                try:
                    if "content" in line:
                        obj = json.loads(line.strip().strip(","))
                        # get candidate teams
                        summ = obj["content"]
                        title = obj["title"]
                        candidates = [team for team, cityname in ec.iteritems()         #cityname can have nicknames
                            if any((namething in summ or namething in title for namething in cityname))]
                        if len(candidates) < 2:
                            num_skipped += 1
                            continue

                        # assume most frequent teams are the ones in the game
                        team1, team2 = None, None
                        if len(candidates) > 2:
                            nospacenames = [team.replace(' ', '') for team in candidates]
                            cand_counts = []
                            for c, candidate in enumerate(candidates):
                                newsumm = summ.replace(candidate, nospacenames[c]) # get City Team first
                                for namething in ec[candidate]:
                                    newsumm = newsumm.replace(namething, nospacenames[c])

                                cand_count = sum((1 for word in newsumm.split() if word == nospacenames[c]))
                                if any((namething in title for namething in ec[candidate])):
                                    cand_count += 100
                                cand_counts.append(cand_count)
                            # get two highest
                            argmaxes = np.argsort(cand_counts)
                            team1, team2 = candidates[argmaxes[-1]], candidates[argmaxes[-2]]
                        else:
                            team1, team2 = candidates[0], candidates[1]
                        if obj["team"] != "General":
                            if obj["team"] != team1 and obj["team"] != team2:
                                num_weird += 1

                        day = datetime.date(obj["date"][0], obj["date"][1], obj["date"][2]) # yr, month, day
                        foundgame = False
                        newobj = None
                        for delt in delts:
                            newday = day + delt
                            scoreboard = nba_py.Scoreboard(month=newday.month, day=newday.day, year=newday.year)
                            linescores = scoreboard.line_score()
                            for i in xrange(0, len(linescores), 2):
                                awaycity1 = linescores.iloc[i][5]#.split()[0]
                                homecity1 = linescores.iloc[i+1][5]#.split()[0]
                                if matches(team1, team2, homecity1, awaycity1):
                                    newobj = add_to_data(day, linescores, i, [summ], None)
                                    foundgame = True
                                    break
                        if not foundgame:
                            print "couldn't find", day, team1, team2
                        g.write("%s\n" % json.dumps(newobj))
                except Exception as ex:
                    print >> sys.stderr, "caught", str(ex)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "sbnation":
        align_sbnation()
    else:
        write_intermediate_json("rotowire_raw")
        align_rotowire()
