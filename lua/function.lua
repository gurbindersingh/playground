function with_defaults(options_table)
    local defaultOptions = {}
    for key, value in pairs(defaultOptions) do 
        options_table[key] = value
    end
    return options_table
end

print(with_defaults({hello="world"}).hello)

