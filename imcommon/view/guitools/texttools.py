def ordinalSuffix(num):
    if num > 9:
        secondToLastDigit = str(num)[-2]
        if secondToLastDigit == '1':
            return 'th'
    lastDigit = num % 10
    if lastDigit == 1:
        return 'st'
    elif lastDigit == 2:
        return 'nd'
    elif lastDigit == 3:
        return 'rd'
    else:
        return 'th'
