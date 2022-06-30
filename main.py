import json
import datetime
import random
import os
import re
import time
import crayons

from collections import defaultdict

WORDS_FOLDER_NAME = 'words'
CASE_INSENSITIVE = True  # useless for now
SMART_LEARNING_NEEDED_SUCCESSES = 4

SAVED_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), WORDS_FOLDER_NAME) + '\\'


def prompt_yes_or_no(question='Please enter'):
    answer = input(f'{question} [y/n]\n')
    if answer.lower() == 'y':
        return True
    elif answer.lower() == 'n':
        return False
    else:
        return prompt_yes_or_no(question=question)


def prompt_nothing():
    answer = input('Press enter to accept.')
    if answer == '':
        return True
    return False


class Quiz:
    def __init__(self):
        self.filename = None
        self.data = {}
        self.is_multiple = False
        self.only_verbs = False
        self.is_relaunch = False
        self.force_quit = False

    @property
    def words(self):
        return self.data['words']

    def restart(self):
        print(crayons.yellow('Restarting...'))
        self.setup()

    def _load(self, filename):
        with open(f'{SAVED_PATH}{filename}', 'r', encoding='utf-8') as fp:
            return json.load(fp)

    def load_from_existing(self, filename, allow_multiple=True):
        if filename == 'all':
            if not allow_multiple:
                raise RuntimeError('You cannot open multiple quized in this mode.')

            for fn in os.listdir(SAVED_PATH):
                if not fn.endswith('.json'):
                    continue

                if fn.startswith('-'):
                    continue

                if fn.startswith('xx-inprogress'):
                    continue

                data = self._load(fn)
                if not self.data:
                    self.data = data
                else:
                    self.data['words'].update(data['words'])
            
            self.is_multiple = True

        elif filename in ('allverbs', 'all_verbs'):
            if not allow_multiple:
                raise RuntimeError('You cannot open multiple quizes in this mode.')

            for fn in os.listdir(SAVED_PATH):
                if not fn.endswith('.json'):
                    continue

                if fn.startswith('-'):
                    continue

                if fn.startswith('xx-inprogress'):
                    continue

                data = self._load(fn)
                if not self.data:
                    self.data = data
                else:
                    self.data['words'].update(data['words'])
            
            self.is_multiple = True
            self.only_verbs = True
        
        elif ', ' in filename:
            if not allow_multiple:
                raise RuntimeError('You cannot open multiple quized in this mode.')

            filenames = filename.split(', ')
            for fn in filenames:
                if not fn.endswith('.json'):
                    fn += '.json'

                if fn.startswith('xx-inprogress'):
                    raise RuntimeError("You can't launch multiple quized already in progress")
                
                data = self._load(fn)
                if not self.data:
                    self.data = data
                else:
                    self.data['words'].update(data['words'])
            
            self.is_multiple = True

        else:
            self.filename = f'{filename}.json'

            if self.filename.startswith('xx-inprogress'):
                self.is_relaunch = True

            data = self._load(self.filename)
            self.data = data

    def save_file(self):
        with open(f'{SAVED_PATH}{self.filename}', 'w', encoding='utf-8') as fp:
            json.dump(self.data, fp, indent=2, default=lambda o: str(o)) 

    def save_word(self, word, solution):
        self.data['words'][word] = solution
        self.save_file()

    def setup_words(self):
        while True:
            inp = input('Enter a new word [GERMAN]: ')
            if inp == '':
                break
            word = inp.strip()

            inp = input('Enter the correct translation [ENGLISH]: ')
            if inp == '':
                continue
            solution = inp.strip()

            if not prompt_nothing():
                print('Ok, the word was not saved')
                continue

            self.save_word(word, solution)

    def setup_new(self):
        self.data = {
            'created_at': str(datetime.datetime.now()),
            'stats': {
                'attempts': 0,
                'word_attempts': 0,
                'word_successes': 0,
                'all_correct_count': 0,
            },
            'words': {},
        }
        # TODO: Tid brukt på quizen
        while True:
            inp = input('Enter a name for the quiz: ')
            inp = inp.lower()
            if os.path.isfile(f'{SAVED_PATH}{inp}.json'):
                print('[ERROR] A file with this name already exists.')
            else:
                self.filename = f'{inp}.json'
                break

        self.setup_words()

    def setup_edit(self):
        name = input('Enter the name of the quiz you wish to edit: ')
        try:
            self.load_from_existing(name.lower())
        except FileNotFoundError:
            print('The quiz was not found.')
            self.restart()

        self.setup_words()

    def save_new_stats(self, len_words, correct_i):
        self.data['stats']['attempts'] += 1
        self.data['stats']['word_attempts'] += len_words
        self.data['stats']['word_successes'] += correct_i

        if len_words == correct_i:
            self.data['stats']['all_correct_count'] += 1

        self.save_file()

    def is_correct(self, a, b):
        a = re.sub(r'[^a-zA-Z0-9 ]', '', a)
        b = re.sub(r'[^a-zA-Z0-9 ]', '', b)

        a = re.sub(r'\(.*\)', '', a)
        b = re.sub(r'\(.*\)', '', b)

        a = a.strip()
        b = b.strip()

        if CASE_INSENSITIVE:
            a = a.lower()
            b = b.lower()

        if a == b:
            return True
        elif a.replace('b', 'ss') == b:
            return True
        elif a.replace('ss', 'b') == b:
            return True
        elif a.replace('ß', 'ss') == b:
            return True
        elif a.replace('ss', 'ß') == b:
            return True
        return False

    def is_correct_list(self, a: list, b: str):
        for word in a:
            res = self.is_correct(word, b)
            if res is True:
                return True
        
        return False

    def run_quiz(self, rand=True, reverse=True):
        if reverse:
            words = [(v, k) for k, v in self.words.items()]
        else:
            words = list(self.words.items())

        len_words = len(words)
        correct_i = 0

        if rand:
            new = random.sample(words, len_words)
        else:
            new = words

        before = time.time()
        for word, solution in new:
            inp = input(f'{word} = ')
            if self.is_correct(solution, inp):
                correct_i += 1
                print(crayons.green('Correct!'))
            else:
                print(f'[{crayons.red("X")}] The answer was "{crayons.yellow(solution)}"')

        done = time.time() - before

        if not self.is_multiple:
            self.save_new_stats(len_words, correct_i)
        print(f'The quiz was finished in {done:.2f}s [{correct_i}/{len_words}]')

    def upper_case_count(self, string):
        return sum(c.isupper() for c in string)

    def smarter_run(self, rand=True, reverse=True):
        if not self.is_relaunch:
            stats = defaultdict(list)
            pre = {}

            if reverse:
                for k, v in self.words.items():
                    if v.lower() not in pre:
                        pre[v.lower()] = {
                            'original': v,
                            'original_upper_count': self.upper_case_count(v),
                            'words': [k],
                            'lowered_words': [k.lower()]
                        }
                    else:
                        upper_count = self.upper_case_count(v)
                        if upper_count > pre[v.lower()]['original_upper_count']:
                            pre[v.lower()]['original'] = v
                            pre[v.lower()]['original_upper_count'] = upper_count

                        if k.lower() not in pre[v.lower()]['lowered_words']:
                            pre[v.lower()]['words'].append(k)
                            pre[v.lower()]['lowered_words'].append(k.lower())

            else:
                for k, v in self.words.items():
                    if k.lower() not in pre:
                        pre[k.lower()] = {
                            'original': k,
                            'original_upper_count': self.upper_case_count(k),
                            'words': [v],
                            'lowered_words': [v.lower()]
                        }
                    else:
                        upper_count = self.upper_case_count(k)
                        if upper_count > pre[k.lower()]['original_upper_count']:
                            pre[k.lower()]['original'] = k
                            pre[k.lower()]['original_upper_count'] = upper_count

                        if v.lower() not in pre[k.lower()]['lowered_words']:
                            pre[k.lower()]['words'].append(v)
                            pre[k.lower()]['lowered_words'].append(v.lower())

            def only_verbs_check(data: dict) -> True:
                if not self.only_verbs:
                    return True

                if data['original'].startswith('to '):
                    return True
                return False

            words = [(d['original'], d['words']) for d in pre.values() if only_verbs_check(d)]

            len_words = len(words)
            correct_i = 0

            if rand:
                new = random.sample(words, len_words)
            else:
                new = words

            cache = []

            before = time.time()
            curr_i = 0

            first_after_relaunch = False

        else:
            ld = self.data

            before = ld['before']
            curr_i = ld['curr_i']
            cache = ld['cache']
            new = ld['new']
            len_words = ld['len_words']
            correct_i = ld['correct_i']
            stats = defaultdict(list, ld['stats'])

            first_after_relaunch = True

        while curr_i < len(new):
            word, solutions = new[curr_i]

            last_tries = stats[word]

            pre_s = 'x'
            combined_answers = '-'.join(solutions)
            cache_entry = f'{word}--{combined_answers}'
            if not first_after_relaunch and cache_entry not in cache:
                cache.append(cache_entry)
                pre_s = len(cache)

            first_after_relaunch = False

            progress_fmt = f'({pre_s}/{len_words})'

            inp = input(f'{progress_fmt} {word} = ').strip()

            if inp.lower().startswith('saveas'):

                data = {
                    'before': before,
                    'curr_i': curr_i,
                    'cache': cache,
                    'new': new,
                    'len_words': len_words,
                    'correct_i': correct_i,
                    'stats': stats
                }

                name = "-".join(inp.lower().split()[1:])
                with open(f'{SAVED_PATH}xx-inprogress-{name}.json', 'w', encoding='utf-8') as fp:
                    json.dump(data, fp, indent=2, default=lambda o: str(o))

                print(crayons.green(f'Saved quiz for later use (xx-inprogress-{name})'))

                self.force_quit = True
                return
            elif inp.lower() in ('ss', 'skip'):
                print(crayons.yellow('Skipping...'))
                curr_i += 1
                continue

            if self.is_correct_list(solutions, inp):
                last_tries.append(True)

                correct_i += 1

                s = ''
                if len(solutions) > 1:
                    p = ', '.join('\''+crayons.green(w)+'\'' for w in solutions)
                    s = f" [{p}]"

                print(f'[{crayons.green("C")}] Correct!{s}')
            else:
                last_tries.append(False)

                if len(solutions) == 1:
                    ss = crayons.yellow(solutions[0])
                else:
                    pp = ', '.join('\''+crayons.yellow(w)+'\'' for w in solutions)
                    ss = f"[{pp}]"

                print(f'[{crayons.red("X")}] The answer was "{ss}"')

            correct = last_tries[-SMART_LEARNING_NEEDED_SUCCESSES:].count(True)
            incorrect = last_tries[-SMART_LEARNING_NEEDED_SUCCESSES:].count(False)

            tup = (word, solutions)

            # If the first guess was correct, put in into the list at the end
            if len(last_tries) == 1 and correct == 1:
                new.append(tup)
            # If we got four in a row on something that we previously failed on, dont add it
            elif len(last_tries) > SMART_LEARNING_NEEDED_SUCCESSES - 1 and last_tries[-SMART_LEARNING_NEEDED_SUCCESSES - 1:].count(True) == SMART_LEARNING_NEEDED_SUCCESSES - 1:
                pass
            else:
                perc = (correct * 100) / len(last_tries[-SMART_LEARNING_NEEDED_SUCCESSES:])
                if 0 <= perc < 20:
                    randint = random.randint(2, 5)
                    new.insert(curr_i+randint, tup)
                    # print(1, randint)
                elif 20 <= perc < 40:
                    randint = random.randint(2, 6)
                    new.insert(curr_i+randint, tup)
                    # print(2, randint)
                elif 40 <= perc <= 50:
                    randint = random.randint(3, 7)
                    new.insert(curr_i+randint, tup)
                    # print(3, randint)
                elif 50 < perc < 100:
                    randint = random.randint(max(len(new) // 3, 0), len(new))
                    new.insert(curr_i+randint, tup)
                    # print(4, randint)
                else:
                    # Its at 100% with at least two tries if we are here so we dont add it
                    # print(5)
                    pass

            # print(new[curr_i:6+curr_i])
            
            stats[word] = last_tries
            curr_i += 1
        
        done = time.time() - before

        print(f'The quiz was finished in {done:.2f}s')

    def setup(self):
        if prompt_yes_or_no('Do you wish to study an existing quiz?'):
            name = input('Enter the name of the existing quiz: ')
            try:
                self.load_from_existing(name.lower())
            except FileNotFoundError:
                print('The quiz was not found.')
                self.restart()
        else:
            if prompt_yes_or_no('Do you wish to edit an existing quiz?'):
                self.setup_edit()
            else:
                self.setup_new()

        if self.is_relaunch:
            smart = True
            rand = True
            reverse = True
        else:
            smart = not not prompt_yes_or_no('Should the quiz be run in smart study mode?')
            rand = not not prompt_yes_or_no('Should the quiz be run in random order?')
            reverse = not not prompt_yes_or_no('Should the languages in the quiz be run in reverse order?')

        while True:
            print('------------------\nThe quiz is now starting\n------------------')
            if smart:
                self.smarter_run(
                    rand=rand,
                    reverse=reverse
                )
            else:
                self.run_quiz(
                    rand=rand,
                    reverse=reverse
                )

            if self.force_quit or not prompt_yes_or_no('Do you wish to study this quiz again?'):
                break

    def run(self):
        self.setup() 


quiz = Quiz()
quiz.run()
