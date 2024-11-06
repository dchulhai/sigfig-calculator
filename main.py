#!/usr/bin/env python3

import asyncio

import pygame
from pygame.locals import *

import numpy as np
import math

import sys

# some colors
WHITE = (255,255,255)
GRAY1 = (64,64,64)
GRAY2 = (128,128,128)
GRAY3 = (192,192,192)
BLACK = (0,0,0)
YELLOW = (242,235,15)
GREEN = (48,252,3)
BLUE = (43,100,207)
RED = (235,52,52)

## Define new number class here ###
class Number():
    def __init__(self, value, numSigFig=None, numDecPl=None):
        '''Initialize the class.'''

        if isinstance(value, str):

            self.string = value.replace(' ', '')
            self.value = float(self.string)

            self.numSigFig = self._numSigFig_()
            self.numDecPl = self._numDecPl_()

        else:
            self.value = value

            if numSigFig is not None:
                self.numSigFig = numSigFig
                self.string = '{0:.{1}e}'.format(self.value,
                        max(self.numSigFig-1,0))
                self.numDecPl = self._numDecPl_()

            elif numDecPl is not None:
                self.numDecPl = numDecPl
                if numDecPl < 0:
                    self.string = '{0}'.format(int(self.value))
                    self.string = ( self.string[:len(self.string)-numDecPl]
                                  + '0'*(numDecPl+1))
                else:
                    self.string = '{0:.{1}f}'.format(self.value, numDecPl)
                self.numSigFig = self._numSigFig_()

            else:
                print ('ERROR: Must enter number of Sig Figs or Dec Pl!')

    @property
    def exponent(self, string=None):
        if string is None:
            string = self.string
        try:
            exponent = int(string.lower().split('e')[1])
        except IndexError:
            exponent = 0
        return exponent

    def __repr__(self):
        '''Representation of the number to print.'''
        if self.numSigFig >= 50 or self.numDecPl >= 50:
            if abs(self.value) > 1e10 or abs(self.value) < 1e-10:
                return '{0:.{1}.e}'.format(self.value, 10).rstrip('0')
            else:
                return '{0:.{1}f}'.format(self.value,
                10).rstrip('0').rstrip('.')
        elif abs(self.value) > 1e10 or abs(self.value) < 1e-10:
            return('{0:.{1}e}'.format(self.value, max(self.numSigFig-1,0)))
        elif self.numDecPl > 0:
            return '{0:.{1}f}'.format(self.value, self.numDecPl)
        elif self.numDecPl < 0:
            string = str(int(round(self.value, self.numDecPl)))
            tempSigFig = self._numSigFig_(string)
            if tempSigFig != self.numSigFig:
                string = '{0:.{1}e}'.format(self.value,
                                             max(self.numSigFig-1,0))
            return string
        else:
            temp = str(int(round(self.value, self.numDecPl)))
            if temp[-1] == '0':
                temp = temp + '.'
            return temp

    def _numSigFig_(self, string=None):
        if string is not None:
            working_string = string.lower().split('e')[0]
        else:
            working_string = self.string.lower().split('e')[0]
        if '.' in working_string:
            return len(working_string.lstrip('0').lstrip('.').lstrip('0').replace('.',''))
        else:
            return len(working_string.lstrip('0').rstrip('0'))

    def _numDecPl_(self):
        working_string = self.string.lower().split('e')[0]
        if '.' in working_string:
            numDecPl = (len(working_string)
                        - np.char.find(working_string, '.')
                        - 1 - self.exponent)
        else:
            for i in range(len(working_string)):
                if working_string[len(working_string)-i-1] != '0':
                    numDecPl = -i - self.exponent
                    break
        return numDecPl

    def __add__(self, other):
        value = self.value + other.value
        numDecPl = min(self.numDecPl, other.numDecPl)
        return Number(value, numDecPl=numDecPl)

    def __sub__(self, other):
        value = self.value - other.value
        numDecPl = min(self.numDecPl, other.numDecPl)
        return Number(value, numDecPl=numDecPl)

    def __mul__(self, other):
        value = self.value * other.value
        numSigFig = min(self.numSigFig, other.numSigFig)
        return Number(value, numSigFig=numSigFig)

    def __truediv__(self, other):
        value = self.value / other.value
        numSigFig = min(self.numSigFig, other.numSigFig)
        return Number(value, numSigFig=numSigFig)

    def __neg__(self):
        return Number(self.value * -1, numSigFig=self.numSigFig)

    def __pow__(self, other):
        return Number(self.value ** other.value, numSigFig=self.numSigFig)

class Exact(Number):

    def __init__(self, Num):
        self.value = Num.value
        self.numSigFig = 100
        self.numDecPl = 100
        self.string = self.__repr__()


# custom math functions
def log(num):
    return Number(np.log10(num.value), numDecPl=num.numSigFig)

def sciExp(num):
    if '.' in num.string:
        return Number(10**(num.value), numSigFig=max(0,num.numDecPl))
    else:
        return Exact(Exact(Number('10'))**num)

def ln(num):
    return Number(np.log(num.value), numDecPl=num.numSigFig)

def exp(num):
    return Number(np.exp(num.value), numSigFig=max(0,num.numDecPl))

def sqrt(num):
    return Number(np.sqrt(num.value), numSigFig=num.numSigFig)


class Calculator():
    def __init__(self):
        self.w = 460
        self.h = 800
        self.screen = pygame.display.set_mode((self.w, self.h))
        self.clock = pygame.time.Clock()

        # 3 font sizes
        self.sm_font = pygame.font.SysFont('Arial', 20, bold=True)
        self.md_font = pygame.font.SysFont('Arial', 36, bold=True)
        self.lg_font = pygame.font.SysFont('Arial', 54, bold=True)

        # strings to store
        self.dispString = []
        self.evalString = []
        self.solution = None
        self.errorString = None

        # booleans
        self.secondFunction = False
        self.answerOnScreen = False
        self.typingNum = False

        # buttons
        buttons = [[None, None, None, None, None],
                   [None, None, None, None, None],
                   [None, None, None, None, None],
                   [None, None, None, None, None],
                   [None, None, None, None, None],
                   [None, None, None, None, None]]

#        buttons[0][0] = self.Buttons('OFF', fontColor1=RED)
        buttons[0][0] = self.Buttons(' ')
        buttons[0][1] = self.Buttons('0', color=GRAY3, fontColor1=BLACK)
        buttons[0][2] = self.Buttons('.', color=GRAY3, fontColor1=BLACK)
        buttons[0][3] = self.Buttons('(-)', color=GRAY3, fontColor1=BLACK,
                                     evalString1=' - ', dispString1=' -')
        buttons[0][4] = self.Buttons('=', text2='Ans', color=GRAY2,
                                     dispString2=' Ans ',
                                     evalString2=' self.solution ')

        buttons[1][0] = self.Buttons('EXACT', dispString1=' EX( ',
                                     evalString1=' Exact( ')
        buttons[1][1] = self.Buttons('1', color=GRAY3, fontColor1=BLACK)
        buttons[1][2] = self.Buttons('2', color=GRAY3, fontColor1=BLACK)
        buttons[1][3] = self.Buttons('3', color=GRAY3, fontColor1=BLACK)
        buttons[1][4] = self.Buttons('+', color=GRAY2, dispString1=' + ')

        buttons[2][0] = self.Buttons('Ln', text2='e^x',
                                     dispString1=' ln( ', dispString2=' exp( ')
        buttons[2][1] = self.Buttons('4', color=GRAY3, fontColor1=BLACK)
        buttons[2][2] = self.Buttons('5', color=GRAY3, fontColor1=BLACK)
        buttons[2][3] = self.Buttons('6', color=GRAY3, fontColor1=BLACK)
        buttons[2][4] = self.Buttons('-', color=GRAY2, dispString1=' - ')

        buttons[3][0] = self.Buttons('log', text2='10^x',
                                     evalString1=' log( ',
                                     evalString2=' sciExp(Number( " ',
                                     dispString1=' log( ',
                                     dispString2=' 10^( ')
        buttons[3][1] = self.Buttons('7', color=GRAY3, fontColor1=BLACK)
        buttons[3][2] = self.Buttons('8', color=GRAY3, fontColor1=BLACK)
        buttons[3][3] = self.Buttons('9', color=GRAY3, fontColor1=BLACK)
        buttons[3][4] = self.Buttons('*', color=GRAY2, dispString1=' * ')

        buttons[4][0] = self.Buttons('x^2', text2='SQRT',
                                     evalString1=' ** Exact(Number("2")) ',
                                     evalString2=' sqrt( ',
                                     dispString1='^2 ', dispString2=' sqrt( ')
        buttons[4][1] = self.Buttons('', color=BLACK)
        buttons[4][2] = self.Buttons('(', dispString1=' ( ')
        buttons[4][3] = self.Buttons(')', dispString1=' ) ')
        buttons[4][4] = self.Buttons('/', color=GRAY2, dispString1=' / ')

        buttons[5][0] = self.Buttons('2ND', text2='2ND', fontColor2=YELLOW)
        buttons[5][1] = self.Buttons('', color=BLACK)
        buttons[5][2] = self.Buttons('DEL')
        buttons[5][3] = self.Buttons('CLEAR')
        buttons[5][4] = self.Buttons('^', dispString1=' ^( ', evalString1=' **( ')

        self.allButtons = buttons


    class Buttons():
        def __init__(self, text1, text2=None, color=GRAY1,
                     fontColor1=WHITE, fontColor2=BLUE, size=(80,80),
                     evalString1=None, evalString2=None,
                     dispString1=None, dispString2=None):

            self.text1 = text1
            self.text2 = text2
            self.color = color
            self.fontColor1 = fontColor1
            self.fontColor2 = fontColor2
            self.size = size

            if dispString1 is None:
                self.dispString1 = self.text1
            else:
                self.dispString1 = dispString1

            if dispString2 is None:
                self.dispString2 = self.text2
            else:
                self.dispString2 = dispString2

            if evalString1 is None:
                self.evalString1 = self.dispString1
            else:
                self.evalString1 = evalString1

            if evalString2 is None:
                self.evalString2 = self.dispString2
            else:
                self.evalString2 = evalString2

        def getDispString(self, secondFunc):
            if secondFunc and self.text2 is not None:
                return self.dispString2
            else:
                return self.dispString1
        def getEvalString(self, secondFunc):
            if secondFunc and self.text2 is not None:
                return self.evalString2
            else:
                return self.evalString1
                        
            
    def drawButtons(self):
        screen = self.screen
        for i in range(5):
            for j in range(6):

                button = self.allButtons[j][i]


                x0 = 6 + i * 92
                y0 = self.h - 98 - j * 92
                pygame.draw.rect(screen, button.color, (x0,y0,80,80),
                             border_radius=20)
                if not self.secondFunction:
                    text = button.text1
                    tColor = button.fontColor1
                elif button.text2 is not None:
                    text = button.text2
                    tColor = button.fontColor2
                else:
                    text = button.text1
                    tColor = button.fontColor1
                if len(text) > 3:
                    text = self.sm_font.render(text, False, tColor)
                elif len(text) > 1:
                    text = self.md_font.render(text, False, tColor)
                else:
                    text = self.lg_font.render(text, False, tColor)
                tx = x0 + 40 - text.get_rect().width // 2
                ty = y0 + 40 - text.get_rect().height // 2
                screen.blit(text, (tx, ty))



    def buttonPressed(self, pos):

        i = int((pos[0] - 6.0)/92.)
        j = int(((self.h - 98 - pos[1])/92.)+0.999)

#        # OFF button
#        if i == 0 and j == 0:
#            pygame.quit()
#            sys.exit()
#            return None

        # Second Function Button
        if i == 0 and j == 5:
            self.secondFunction = not self.secondFunction
            return None

        # Number, decimal keys
        if (i > 0 and i < 4 and j >= 0 and j <= 3):
            buttonText = self.allButtons[j][i].getDispString(self.secondFunction)
            evalStText = self.allButtons[j][i].getEvalString(self.secondFunction)
            if not self.typingNum:
                evalStText = ' Number( " ' + evalStText
                self.typingNum = True
            if i == 3 and j == 0:
                buttonText = '-'
                evalStText = ' - '
            if self.answerOnScreen:
                self.dispString = [buttonText]
                self.evalString = [evalStText]
                self.answerOnScreen = False
            else:
                self.dispString.append(buttonText)
                self.evalString.append(evalStText)

        # DEL button
        elif i == 2 and j == 5:
            self.dispString = self.dispString[:-1]
            self.evalString = self.evalString[:-1]

        # CLEAR button
        elif i == 3 and j == 5:
            self.dispString = []
            self.evalString = []
            self.typingNum = False
            self.errorString = None
            self.solution = None


        ### THIS IS THE EVALUATE BUTTON ##
        elif i == 4 and j == 0 and not self.secondFunction:
            fullEvalString = ''.join(self.evalString)
            if self.typingNum:
                fullEvalString += ' " ) '
                self.typingNum = False

            openPar = 0
            for s in fullEvalString:
                if s == '(': openPar += 1
            closePar = 0
            for s in fullEvalString:
                if s == ')': closePar += 1
            if openPar > closePar:
                fullEvalString += ' " ) '

            try:
                self.solution = eval(fullEvalString)
                self.answerOnScreen = True
            except SyntaxError:
                self.errorString = 'Syntax Error'
                print (fullEvalString)
            except UnboundLocalError:
                self.errorString = 'Code Error'
                print (fullEvalString)
            except ZeroDivisionError:
                self.errorString = 'Zero Division'
                print (fullEvalString)
            except:
                self.errorString = 'ERROR'
                print (fullEvalString)

        # all other buttons
        else:
            dispString = self.allButtons[j][i].getDispString(self.secondFunction)
            evalString = self.allButtons[j][i].getEvalString(self.secondFunction)

            if self.typingNum:
                evalString = ' " ) ' + evalString
                self.typingNum = False

            if self.answerOnScreen:
                if ((i == 4 and j > 0)
                  or (i == 0 and j == 4 and not self.secondFunction)):
                    self.dispString = ['Ans ', dispString]
                    self.evalString = ['self.solution ', evalString]
                else:
                    self.dispString = [dispString]
                    self.evalString = [evalString]
                self.answerOnScreen = False
            else:
                self.dispString.append(dispString)
                self.evalString.append(evalString)

        self.secondFunction = False
        return None


    def displayScreen(self):

        # show the input string on top in gray
        fullDisplayString = ''.join(self.dispString)
        displayText = self.sm_font.render(fullDisplayString, False, GRAY3)
        tx = 440 - displayText.get_rect().width
        self.screen.blit(displayText, (tx, 20))

        # show the solution string in yellow
        if self.solution is not None:
            solutionString = self.solution.__repr__()
            solutionText = self.lg_font.render(solutionString,
                                               False, YELLOW)
            tx = 440 - solutionText.get_rect().width
            self.screen.blit(solutionText, (tx, 80))


            # show the full number
            value = self.solution.value
            if abs(value) > 1e10 or abs(value) < 1e-10:
                fullNumSt = '{0:.{1}e}'.format(value, 10).rstrip('0')
            else:
                fullNumSt = '{0:.{1}f}'.format(value, 10).rstrip('0')
            fullNumText = self.sm_font.render('full answer: ' + fullNumSt,
                            False, YELLOW)
            self.screen.blit(fullNumText, (20, 160))

            # show num of Sig Fig
            numSigFig = self.solution.numSigFig
            if numSigFig < 50:
                sigFigText = self.sm_font.render('sig figs: {0}'.format(
                    numSigFig), False, GREEN)
            else:
                sigFigText = self.sm_font.render('sig figs: oo',
                        False, GREEN)
            self.screen.blit(sigFigText, (20, 190))


            # show precision on the screen
            numDecPl = self.solution.numDecPl
            if numDecPl >= 50:
                precisionStr = 'oo'
            elif abs(numDecPl) > 10:
                precisionStr = '{0:.0e}'.format(10.0 ** (-1 * numDecPl))
            elif numDecPl < 0:
                precisionStr = '1' + '0' * abs(numDecPl)
            elif numDecPl > 0:
                precisionStr = '0.' + '0'*(numDecPl-1) + '1'
            else:   
                precisionStr = '1'
            precisionStr = 'precision: ' + precisionStr
            precisionText = self.sm_font.render(precisionStr, False, GREEN)
            self.screen.blit(precisionText, (230, 190))

        elif self.errorString is not None:
            errorText = self.lg_font.render(self.errorString,
                                               False, RED)
            tx = 440 - errorText.get_rect().width
            self.screen.blit(errorText, (tx, 80))


pygame.init()
pygame.font.init()
calc = Calculator()


async def main(calc):

    screen = calc.screen
    height = calc.h
    width = calc.w

    while True:

        # get game events
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == MOUSEBUTTONUP:
                pos = pygame.mouse.get_pos()
                calc.buttonPressed(pos)

        # fill screen
        screen.fill(BLACK)

        # draw buttons
        calc.drawButtons()

        # display screen info
        calc.displayScreen()

        calc.clock.tick()
        pygame.display.update()
        await asyncio.sleep(0)

asyncio.run(main(calc))

