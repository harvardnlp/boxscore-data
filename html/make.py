import json
import pandas
import argparse
import sys


def print_table(f, table, seen):
    f.write("<table border=1 class=\"table table-hover table-striped table-bordered\">")
    f.write("<tr><th></th>")
    for col in table.columns:
        f.write("<th>%s</th>"%(col))
    f.write("</tr>")
    for row in table.iterrows():
        row_id = row[0].replace(" ", "_").replace("'", "\\'").replace(".", "")
        f.write("<tr class=\"off_row\" id=\"%s\"> <th>%s</th>"%(row_id, row[0]))
        for k, r in enumerate(row[1]):
            key = "%s_%s_%s" %(row_id, table.columns[k], str(r).replace("'", "\\'") )
            key = key.replace(".", "")
            f.write("<td id=\"%s\" onclick=\"tab_select('%s')\">%s</td>"%(key, key, r))
            seen.setdefault(str(r), []).append([key, row_id])
        f.write("</tr>")
    f.write("</table>")


def main(arguments):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('infile', help="Input file",
                        type=argparse.FileType('r'))
    # parser.add_argument('-o', '--outfile', help="Output file",
    #                     default=sys.stdout, type=argparse.FileType('w'))

    args = parser.parse_args(arguments)


    data = json.load(args.infile)

    order = ["FIRST_NAME", "SECOND_NAME", "H/V", 'POS', 'MIN', 'PTS', 'REB', 'AST', 'BLK', 'TO', 'PF', 'STL', 'DREB', 'OREB', 'FGM',  'FGA', 'FG_PCT', 'FTM',   'FTA','FT_PCT','FG3M', 'FG3A','FG3_PCT']
    order2 = ["NAME", "CITY", "WINS", "LOSSES", "PTS", "QTR1", "QTR2", "QTR3", "QTR4", "AST", "REB", "TOV", "FG_PCT", "FT_PCT", "FG3_PCT"]

    for game_num, game in enumerate(data):
        cols = {k: k.split("-")[1] if not k[-1].isdigit()
                else k.split("_")[-1] for k in game["vis_line"]}

        stats = pandas.DataFrame(game["box_score"]).set_index("PLAYER_NAME")
        # game["home_line"]["NAME"] = game["home_name"]
        # game["vis_line"]["NAME"] = game["vis_name"]
        line = pandas.DataFrame({game["home_name"] : game["home_line"], game["vis_name"]: game["vis_line"]})

        stats["H/V"] = (stats["TEAM_CITY"] == game["home_city"] ).map(lambda a: "H" if a else "V")
        # del stats["FIRST_NAME"]
        # del stats["SECOND_NAME"]
        del stats["TEAM_CITY"]

        stats = stats.rename(columns={"START_POSITION": "POS"})
        stats = stats[order]
        stats = stats.applymap(lambda a: int(a) if a[0].isdigit() else a)
        stats = stats.sort_values(by=["PTS", "REB"], ascending=False)
        line= line.transpose().rename(columns =cols)
        # del line["NAME"]
        line = line[order2]
        stats = stats.applymap(lambda a: "" if a == "N/A" else a)



        f = open("game"+str(game_num)+".html", "w")
        f.write("""<head>
<link href="https://maxcdn.bootstrapcdn.com/font-awesome/4.6.3/css/font-awesome.min.css" rel="stylesheet"
          integrity="sha384-T8Gy5hrqNKT+hzMclPo118YTQO6cYprQmhrYwIiQ/3axmI1hQomh7Ud2hPOy8SP1" crossorigin="anonymous">
    <link href="https://maxcdn.bootstrapcdn.com/bootswatch/3.3.6/cosmo/bootstrap.min.css" rel="stylesheet"
          integrity="sha384-OiWEn8WwtH+084y4yW2YhhH6z/qTSecHZuk/eiWtnvLtU+Z8lpDsmhOKkex6YARr" crossorigin="anonymous">
  <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.12.4/jquery.min.js"></script>
  <script src="http://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js"></script>
<script src=\"select.js\"></script>
    <style>
        a {
            color: black;
        }

        a:hover {
            color: black;
            font-weight: 500;
        }
        .off_row {
        display: none;
        }

        .ambi_row {
        display: table-row;
        }

        .sel_word {
            color: blue;

            background: yellow;
        }
        .ambi_word {
            color: red;
        }

        .fin_word {
            color: grey;
            # background: grey;
        }

        .sel_tab {
            color: red;
            font-weight: bold;
            background: yellow;
        }
        .fin_tab {
            color: grey;
        }

        .ambi_tab {
            color: red;
        font-weight: bold;
        background: yellow;
        }
        .sum {
            cursor: pointer;
        }

        .table {
            cursor: pointer;
        }
        .sum {
        padding-left: 200px;
        padding-right: 200px;

        font-size: 20px;
        }
    </style>
</head>
<body>
""")
        f.write("<br><div class=\"content\">")
        seen = {}

        f.write("<div class=\"sum\">")
        for i, w in enumerate(game["summary"]):
            id = "sum%d_%s"%(i,w)
            f.write("<span id=\"%s\" onclick=\"word_select('%s')\">%s</span> " % (id, id, w))
            # if w.strip() == ".":
            #     f.write("<br>")
        f.write("</div>")
        f.write("<center> <input type='button' value=\"skip\" onclick=\"tab_select('')\"></center>")
        print_table(f, line, seen)
        print_table(f, stats, seen)

        ambi_links = {}
        links = {}
        ord = {}
        last = [""]
        for i, w in enumerate(game["summary"]):
            id = "sum%d_%s"%(i,w)
            matches = seen.get(w, [])
            if len(matches) == 1:
                links[id] = matches[0]
            if len(matches) >= 1:
                for l in last:
                    ord[l] = id
                last = []
            if len(matches) >= 1:
                last.append(id)
                ambi_links[id] = matches

        f.write("<br> <center><textarea cols=200 rows=10 editable=0 id=\"show\"></textarea></center>")
        f.write("\n<script>init(%s, %s, %s)</script>"%(json.dumps(links), json.dumps(ambi_links), json.dumps(ord)))
        f.write("</div></body>")
        f.close()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
