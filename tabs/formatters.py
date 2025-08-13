"""
Standardized number formatters for all tab files
Provides consistent formatting with center alignment and comma separation
"""

from st_aggrid import JsCode

# Standardized formatters with center alignment and comma separation
currency_formatter = JsCode("""
    function(params) {
        if (params.value === null || typeof params.value === 'undefined') {
            return '';
        }
        return params.value.toLocaleString('en-US');
    }
""")

percentage_formatter = JsCode("""
    function(params) {
        if (params.value === null || typeof params.value === 'undefined') {
            return '';
        }
        return (params.value * 100).toFixed(2) + '%';
    }
""")

number_formatter = JsCode("""
    function(params) {
        if (params.value === null || typeof params.value === 'undefined') {
            return '';
        }
        return params.value.toLocaleString('en-US');
    }
""")

# Formatter for large numbers (millions, thousands)
large_number_formatter = JsCode("""
    function(params) {
        if (params.value === null || typeof params.value === 'undefined') {
            return '';
        }
        const value = params.value;
        if (value >= 1000000) {
            return (value / 1000000).toFixed(1) + 'M';
        } else if (value >= 1000) {
            return (value / 1000).toFixed(1) + 'K';
        }
        return value.toLocaleString('en-US');
    }
""")

# Decimal formatter for rates and ratios
decimal_formatter = JsCode("""
    function(params) {
        if (params.value === null || typeof params.value === 'undefined') {
            return '';
        }
        return params.value.toFixed(2);
    }
""")

# Standard cell style for center alignment
center_aligned_style = {
    'textAlign': 'center'
}

# Function to get standard column configuration
def get_standard_column_config(column_name, header_name, width=120, min_width=100, formatter_type='number'):
    """
    Get standardized column configuration with consistent formatting
    
    Args:
        column_name: Column name in dataframe
        header_name: Display name in table header
        width: Column width (default 120)
        min_width: Minimum column width (default 100)
        formatter_type: Type of formatter ('number', 'currency', 'percentage', 'large_number', 'decimal')
    
    Returns:
        Dictionary with column configuration
    """
    formatters = {
        'number': number_formatter,
        'currency': currency_formatter,
        'percentage': percentage_formatter,
        'large_number': large_number_formatter,
        'decimal': decimal_formatter
    }
    
    return {
        'field': column_name,
        'headerName': header_name,
        'width': width,
        'minWidth': min_width,
        'valueFormatter': formatters.get(formatter_type, number_formatter),
        'cellStyle': center_aligned_style,
        'headerClass': 'center-header'
    }

# CSS for center-aligned headers
center_header_css = """
    .center-header .ag-header-cell-label {
        justify-content: center;
        text-align: center;
    }
    .ag-cell {
        text-align: center;
    }
"""