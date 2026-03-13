"""
Ollama/OpenAI-style Tool Definitions for SPEAR MCP Tools and Plotting
"""

# Tool definitions in OpenAI-compatible format (used by Ollama)
OLLAMA_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_plot",
            "description": "Create a plot from data you already have. DO NOT query data again - use values from previous tool results. Pass a JSON string with: plot_type, data (x and y arrays), title, xlabel, ylabel, and style with metadata. CONVERT UNITS FIRST: multiply precipitation by 86400 (kg/m²/s to mm/day), subtract 273.15 from temperature (K to °C).",
            "parameters": {
                "type": "object",
                "properties": {
                    "plot_config": {
                        "type": "string",
                        "description": "JSON string. Example for monthly precipitation: {\"plot_type\": \"bar\", \"data\": {\"x\": [\"Jan\", \"Feb\", \"Mar\", \"Apr\", \"May\", \"Jun\", \"Jul\", \"Aug\", \"Sep\", \"Oct\", \"Nov\", \"Dec\"], \"y\": [2.97, 0.15, 0.95, 2.69, 4.32, 6.78, 4.48, 3.60, 5.85, 4.19, 3.05, 0.53]}, \"title\": \"Monthly Precipitation - Mexico City 2028\", \"xlabel\": \"Month\", \"ylabel\": \"Precipitation (mm/day)\", \"style\": {\"color\": \"steelblue\", \"metadata\": {\"location\": \"Mexico City\", \"coordinates\": \"19.25N, 260.94E\", \"scenario\": \"SSP5-8.5\", \"year\": \"2028\"}}}"
                    }
                },
                "required": ["plot_config"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_s3_file_metadata_only",
            "description": "Get metadata about a SPEAR NetCDF file. By default uses fast mode which extracts info from the filename and S3 (file size, date range, variable, etc.) without opening the file. Set include_full_details=true to get complete dimension and coordinate information (slower). Rarely needed - prefer query_netcdf_data for actual data retrieval.",
            "parameters": {
                "type": "object",
                "properties": {
                    "scenario": {
                        "type": "string",
                        "description": "Either 'historical' or 'scenarioSSP5-85'"
                    },
                    "ensemble_member": {
                        "type": "string",
                        "description": "Ensemble member (e.g., 'r1i1p1f1', 'r15i1p1f1')"
                    },
                    "frequency": {
                        "type": "string",
                        "description": "'Amon' for monthly, 'day' for daily"
                    },
                    "variable": {
                        "type": "string",
                        "description": "Variable name (e.g., 'tas', 'pr', 'ua')"
                    },
                    "grid": {
                        "type": "string",
                        "description": "Grid type (typically 'gr3')"
                    },
                    "version": {
                        "type": "string",
                        "description": "Data version (typically 'v20210201')"
                    },
                    "filename": {
                        "type": "string",
                        "description": "Optional: exact filename if known (e.g., 'pr_day_GFDL-SPEAR-MED_historical_r4i1p1f1_gr3_19210101-19301231.nc'). If provided, uses this filename directly."
                    },
                    "include_full_details": {
                        "type": "boolean",
                        "description": "If true, opens the file to get full coordinate/dimension details (slower for large files). Default is false for fast mode."
                    }
                },
                "required": ["scenario", "variable"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_netcdf_data",
            "description": "Query and retrieve actual climate data from SPEAR NetCDF files with optional spatial and temporal subsetting. Use this to get real climate data values for analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "variable": {
                        "type": "string",
                        "description": "Variable name (e.g., 'tas' for temperature, 'pr' for precipitation)"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM format (e.g., '2020-01'). Leave null for beginning of dataset."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM format (e.g., '2021-12'). Leave null for end of dataset."
                    },
                    "lat_range": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "[min_latitude, max_latitude] in degrees. E.g., [30, 50] for mid-latitudes. Leave null for global."
                    },
                    "lon_range": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "[min_longitude, max_longitude] in degrees. E.g., [-120, -80] for North America. Leave null for global."
                    },
                    "scenario": {
                        "type": "string",
                        "description": "Either 'historical' or 'scenarioSSP5-85'"
                    },
                    "ensemble_member": {
                        "type": "string",
                        "description": "Ensemble member (default: 'r1i1p1f1')"
                    },
                    "frequency": {
                        "type": "string",
                        "description": "'Amon' for monthly, 'day' for daily (default: 'Amon')"
                    },
                    "grid": {
                        "type": "string",
                        "description": "Grid type (default: 'gr3')"
                    },
                    "version": {
                        "type": "string",
                        "description": "Data version (default: 'v20210201')"
                    },
                    "chunk_index": {
                        "type": "integer",
                        "description": "Which chunk to return if data is chunked (default: 0)"
                    }
                },
                "required": ["variable"]
            },
        },
    },
    # ========== CMIP6 Zarr Tools ==========
    {
        "type": "function",
        "function": {
            "name": "test_cmip6_connection",
            "description": "Test connection to CMIP6 Zarr store on AWS S3 and return basic store information (dimensions, variables, coordinates). Use this to verify CMIP6 data access is working.",
            "parameters": {
                "type": "object",
                "properties": {
                    "zarr_path": {
                        "type": "string",
                        "description": "Optional S3 path to Zarr store. If not provided, uses default CMIP6 GFDL-CM4 historical data."
                    }
                },
                "required": []
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_zarr_store_info",
            "description": "Get metadata from CMIP6 Zarr store without loading data arrays. Returns store size, dimensions, coordinates, and variable information. Set include_full_details=true for complete coordinate/variable details (slower).",
            "parameters": {
                "type": "object",
                "properties": {
                    "zarr_path": {
                        "type": "string",
                        "description": "Optional S3 path to Zarr store. If not provided, uses default CMIP6 GFDL-CM4 historical data."
                    },
                    "include_full_details": {
                        "type": "boolean",
                        "description": "If true, includes detailed coordinate and variable information (slower). Default is false for fast mode."
                    }
                },
                "required": []
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_zarr_data",
            "description": "Query and retrieve climate data from CMIP6 Zarr store with spatial and temporal subsetting. Use this to get actual CMIP6 climate data values. Data is from GFDL-CM4 historical experiment (1850-2014).",
            "parameters": {
                "type": "object",
                "properties": {
                    "variable": {
                        "type": "string",
                        "description": "Variable name (e.g., 'tas' for near-surface air temperature)"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM format (e.g., '1850-01'). Leave null for beginning of dataset."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM format (e.g., '2014-12'). Leave null for end of dataset."
                    },
                    "lat_range": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "[min_latitude, max_latitude] in degrees. E.g., [30, 50] for mid-latitudes. Leave null for global."
                    },
                    "lon_range": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "[min_longitude, max_longitude] in degrees. E.g., [-120, -80] for North America. Leave null for global."
                    },
                    "zarr_path": {
                        "type": "string",
                        "description": "Optional S3 path to Zarr store. If not provided, uses default CMIP6 GFDL-CM4 historical data."
                    }
                },
                "required": ["variable"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_zarr_summary_statistics",
            "description": "Get summary statistics (min, max, mean, std) for CMIP6 Zarr data without returning full arrays. More efficient than loading all data when you only need statistics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "variable": {
                        "type": "string",
                        "description": "Variable name (e.g., 'tas' for temperature)"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM format (e.g., '1850-01')"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM format (e.g., '2014-12')"
                    },
                    "lat_range": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "[min_latitude, max_latitude] in degrees"
                    },
                    "lon_range": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "[min_longitude, max_longitude] in degrees"
                    },
                    "zarr_path": {
                        "type": "string",
                        "description": "Optional S3 path to Zarr store"
                    }
                },
                "required": ["variable"]
            },
        },
    },
]
