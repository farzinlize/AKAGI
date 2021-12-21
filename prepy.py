import os, sys

STR_SECTION = '#->'
END_SECTION = '#--'

ACTIVATE   = 'a'
DEACTIVATE = 'd'


def deactivate_line(line:str):
    tokens = line.split()
    if not tokens:return line
    if tokens[0].startswith('#'):return line
    location = next(idx for idx, chr in enumerate(line) if not chr.isspace())
    return line[:location] + '# ' + line[location:]


def activate_line(line:str):
    tokens = line.split()
    if not tokens:return line
    if not tokens[0].startswith('#'):return line
    hashtag = line.find('#')
    start = hashtag + 1 + next(idx for idx, chr in enumerate(line[hashtag+1:]) if not chr.isspace())
    return line[:hashtag] + line[start:]


def toggle_tag(tag, files=None, toggle=ACTIVATE):
    if not files:files = [py for py in os.listdir() if py.endswith('.py')]
    for file in files:

        # first read code
        with open(file, 'r') as origin:data = origin.readlines()

        with open(file, 'w') as result:
            mode = 'nop'
            for line in data:
                if STR_SECTION in line and tag in line:mode = toggle;result.write(line);continue
                if END_SECTION in line                :mode = 'nop' ;result.write(line);continue

                if   mode == 'nop'     :result.write(line)
                elif mode == ACTIVATE  :result.write(activate_line  (line))
                elif mode == DEACTIVATE:result.write(deactivate_line(line))


if __name__ == '__main__':
    tag = sys.argv[1]
    if len(sys.argv) >= 3:toggle = sys.argv[2]
    else                 :toggle = ACTIVATE
    if len(sys.argv) >= 4:files = sys.argv[3:]
    else                 :files = None

    if not toggle in [ACTIVATE, DEACTIVATE]:print("[error] use a/d as toggle for activate or deactivate tag");exit()
    print(f"prepy starting to toggle ({toggle}) tag ({tag}) in files (None for every .py file in directory): {files}")
    toggle_tag(tag, files, toggle)