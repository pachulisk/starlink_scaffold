

def is_chinese(uchar):
  """
  判断一个unicode是否为汉字
  """
  if '\u4e00' <= uchar <= '\u9fff':
      return True
  else:
      return False

def is_number(uchar):
  """
  判断一个unicode是否为数字
  """
  if '\u0030' <= uchar <= '\u0039':
      return True
  else:
      return False
  
def is_qnumber(uchar):
   """
   判断一个unicode是否为全角数字
   """
   if '\uff10' <= uchar <= '\uff19':
       return True
   else:
       return False

def is_alphabet(uchar):
  """
  判断一个unicode是否为半角英文字母
  """
  if ('\u0041' <= uchar <= '\u005a') or ('\u0061' <= uchar <= '\u007a'):
      return True
  else:
      return False
  
def is_qalphabet(uchar):
  """
  判断一个unicode是否为全角英文字母
  """
  if ('\uff21' <= uchar <= '\uff3a') or ('\uff41' <= uchar <= '\uff5a'):
      return True
  else:
      return False

def is_other(uchar):
   """
   判断是否非汉字、数字和英文字符
   """
   if not (is_chinese(uchar) or is_number(uchar) or is_qnumber(uchar) or is_alphabet(uchar) or is_qalphabet(uchar)):
       return True
   else:
       return False

def b2q(uchar):
   """
   单个字符，半角转化全角
   """
   inside_code = ord(uchar)
   if inside_code < 0x0020 or inside_code > 0x7e:
       return uchar
   if inside_code == 0x0020:
       inside_code = 0x3000
   else:
       inside_code += 0xfee0
   return chr(inside_code)

def q2b(uchar):
    """
    单个字符，全角转换半角
    """
    inside_code = ord(uchar)
    if inside_code == 0x3000:
        inside_code = 0x0020
    else:
        inside_code -= 0xfee0
    if inside_code < 0x0020 or inside_code > 0x7e:
        return uchar
    return chr(inside_code)

def stringq2b(uchars):
    """
    全部字符串全角转换半角
    """
    return "".join([q2b(uchar) for uchar in uchars])