import random

# https://docs.python.org/3/library/string.html#format-string-syntax
# https://docs.python.org/3/library/string.html#format-specification-mini-language

"""====================== String Formatting Options ===========================
replacement_field  ::=  "{" [field_name] ["!" conversion] [":" format_spec] "}"
field_name         ::=  arg_name ("." attribute_name | "[" element_index "]")*
arg_name           ::=  [identifier | digit+]
attribute_name     ::=  identifier
element_index      ::=  digit+ | index_string
index_string       ::=  <any source character except "]"> +
conversion         ::=  "r" | "s" | "a"
format_spec        ::=  [[fill]align][sign][#][0][width][grouping_option]
                        [.precision][type]
fill               ::=  <any character>
align              ::=  "<" | ">" | "=" | "^"
sign               ::=  "+" | "-" | " "
width              ::=  digit+
grouping_option    ::=  "_" | ","
precision          ::=  digit+
type               ::=  "b" | "c" | "d" | "e" | "E" | "f" | "F" | "g" | "G" |
                        "n" | "o" | "s" | "x" | "X" | "%"
 """

"""=========================== Alignment Option ===============================

'<'     Forces the field to be left-aligned within the available space (this is
        the default for most objects).

'>'     Forces the field to be right-aligned within the available space (this is
        the default for numbers).

'='     Forces the padding to be placed after the sign (if any) but before the
        digits. This is used for printing fields in the form ‘+000000120’. This
        alignment option is only valid for numeric types. It becomes the default
        for numbers when ‘0’ immediately precedes the field width.

'^'   Forces the field to be centered within the available space.
"""

"""============================= Sign Options =================================

'+'     Indicates that a sign should be used for both positive as well as
        negative numbers.

'-'     Indicates that a sign should be used only for negative numbers (this
        is the default behavior).

space   Indicates that a leading space should be used on positive numbers, and
        a minus sign on negative numbers.
"""

a = random.random()
print(f"a = {a: >10,.4f}")
print(f"Total: {'$ ' + str(round(a, 4)) : >10}")
print(f"Total: {'$ ' + f'{a:.4f}': >10}")
