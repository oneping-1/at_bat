from typing import List

def air_out(words: List[str]):
    for word in words:
        if word == 'pitcher':
            return '1'
        if word == 'catcher':
            return '2'
        if word == 'first':
            return '3'
        if word == 'second':
            return '4'
        if word == 'third':
            return '5'
        if word == 'short':
            return '6'
        if word == 'left':
            return '7'
        if word == 'center':
            return '8'
        if word == 'right':
            return '9'

def ground_out(words: List[str]):
    order = []
    
    for word in words:
        if word == 'pitcher':
            order.append('1')
        if word == 'catcher':
            order.append('2')
        if word == 'first':
            order.append('3')
        if word == 'second':
            order.append('4')
        if word == 'third':
            order.append('5')
        if word == 'shortstop':
            order.append('6')
            
    text = ''
    
    for i in order:
        text = f'{text}{i}-'
    
    if text == '3-':
        text = '3U-'
    
    return text[:-1]

def scorebook(text: str):
    if text is None:
        return None
    
    text = text.split(' ')
    
    
    for i, word in enumerate(text):
        word = word.strip('.')
        word = word.strip(',')
        
        
        if word == 'singles':
            return '1B'
        if word in ('double', 'doubles'): # Ground rule double
            return '2B'
        if word == 'triples':
            return '3B'
        if word == 'homers':
            return 'HR'
        
        if word == 'walks':
            return 'BB'
        
        if word in ('swinging', 'tip', 'foul'):
            return 'Ks'
        
        if word == 'called':
            return 'Kc'
        
        if word == 'lines':
            return f'L{air_out(text)}'
        
        if word == 'flies':
            return f'F{air_out(text)}'
        
        if word == 'pops':
            return f'P{air_out(text)}'
        
        
        if word == 'hit':
            return 'HBP'
        
        try:
            next_word = text[i+1]
        except IndexError:
            return None
        next_word = next_word.strip('.')
        next_word = next_word.strip(',')
        
        if word == 'error':
            return f'E{air_out(text)}'
        
        if (word == 'sacrifice') and (next_word == 'fly'):
            return f'SF{air_out(text)}'
        
        if (word == 'sacrifice') and (next_word == 'bunt'):
            return 'SAC'           
        
        if (word == 'grounds') or (word == "fielder's" and next_word == 'choice'):
            return ground_out(text)
            
    return None

if __name__ == '__main__':
    x = 'Nicky Lopez hits a sacrifice bunt. Evan Carter scores. Jake Burger to 2nd. Nicky Lopez to 1st.'
    scorebook(x)