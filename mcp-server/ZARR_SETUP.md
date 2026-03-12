# CMIP6 Zarr MCP Server Setup

This is a modified version of the SPEAR MCP server adapted to work with CMIP6 Zarr data on AWS S3.

## What Changed

### Original Setup (NetCDF)
- **Data format:** NetCDF (.nc) files
- **Dataset:** SPEAR (NOAA-GFDL)
- **S3 Bucket:** `noaa-gfdl-spear-large-ensembles-pds`
- **File structure:** Multiple individual .nc files with date ranges
- **Engine:** `h5netcdf` via `xr.open_dataset()`

### New Setup (Zarr)
- **Data format:** Zarr store (directory-based)
- **Dataset:** CMIP6 GFDL-CM4 historical
- **S3 Bucket:** `cmip6-pds`
- **Path:** `CMIP6/CMIP/NOAA-GFDL/GFDL-CM4/historical/r1i1p1f1/Amon/tas/gr1/v20180701/`
- **File structure:** Single Zarr store (consolidated metadata)
- **Engine:** `zarr` via `xr.open_zarr()`

## New Files Added

1. **`src/spear_mcp/tools_zarr.py`** - New tools for Zarr data access:
   - `test_cmip6_connection()` - Test S3 connection to CMIP6 Zarr store
   - `get_zarr_store_info()` - Get Zarr metadata without loading data
   - `load_zarr_dataset()` - Load Zarr with lazy evaluation
   - `query_zarr_data()` - Query with spatial/temporal subsetting
   - `get_zarr_summary_statistics()` - Get statistics without full data load

2. **`ZARR_SETUP.md`** - This documentation file

3. **`test_zarr_connection.py`** - Standalone test script

## Modified Files

1. **`src/spear_mcp/server.py`** - Added Zarr tool registrations
2. **`pyproject.toml`** - Added `zarr>=2.18.0` dependency

## Testing the New Setup

### 1. Install Dependencies

```bash
cd ~/spear-mcp-edit
uv sync  # or: pip install -e .
```

### 2. Run Test Script

```bash
python ~/test_zarr_connection.py
```

This will test:
- ✅ Connection to CMIP6 S3 bucket
- ✅ Zarr store metadata access
- ✅ Small data query (1 year, small region)
- ✅ Summary statistics calculation

### 3. Start the MCP Server

```bash
cd ~/spear-mcp-edit
uv run python -m spear_mcp
```

The server will start on port 8000 with both NetCDF (SPEAR) and Zarr (CMIP6) tools available.

## Available Zarr Tools

### `test_cmip6_connection()`
Tests connection to CMIP6 Zarr store and returns basic info.

**Example:**
```python
test_cmip6_connection()
# Returns: status, dimensions, variables, coordinates
```

### `get_zarr_store_info()`
Gets metadata without loading data arrays.

**Parameters:**
- `zarr_path` (optional): S3 path to Zarr store
- `include_full_details` (bool): Include coordinate/variable details

**Example:**
```python
get_zarr_store_info(include_full_details=True)
```

### `query_zarr_data()`
Main data extraction tool with subsetting.

**Parameters:**
- `variable`: Variable name (default: "tas")
- `start_date`: Start date (e.g., "1850-01")
- `end_date`: End date (e.g., "2014-12")
- `lat_range`: [min, max] latitude
- `lon_range`: [min, max] longitude
- `zarr_path` (optional): Custom Zarr store path

**Example:**
```python
query_zarr_data(
    variable="tas",
    start_date="1850-01",
    end_date="1860-12",
    lat_range=[30, 50],
    lon_range=[-120, -80]
)
```

### `get_zarr_summary_statistics()`
Computes statistics without returning full data arrays.

**Parameters:** Same as `query_zarr_data()`

**Returns:** min, max, mean, std

**Example:**
```python
get_zarr_summary_statistics(
    variable="tas",
    start_date="1850-01",
    end_date="2014-12",
    lat_range=[30, 50],
    lon_range=[-120, -80]
)
```

## Key Advantages of Zarr

1. **Lazy loading** - Only downloads data when accessed
2. **Chunked storage** - Efficient for subsetting
3. **No file listing** - Single store vs. multiple NC files
4. **Faster metadata** - Consolidated metadata in `.zmetadata`

## Current Default Dataset

The tools are configured for:
- **Model:** GFDL-CM4
- **Experiment:** historical
- **Ensemble:** r1i1p1f1
- **Variable:** tas (near-surface air temperature)
- **Frequency:** Amon (monthly)
- **Grid:** gr1
- **Version:** v20180701

To use a different Zarr store, pass the full S3 path to any function:
```python
zarr_path = "s3://cmip6-pds/CMIP6/CMIP/NOAA-GFDL/GFDL-CM4/[experiment]/[ensemble]/[freq]/[var]/[grid]/[version]/"
```

## Next Steps

1. ✅ Test the connection with `test_zarr_connection.py`
2. ✅ Start the MCP server
3. Connect your chatbot to the MCP server
4. Try queries through the chatbot interface

## Troubleshooting

### Connection errors
- Check internet connectivity
- Verify AWS credentials (should work with anonymous access)
- Confirm S3 path exists: `aws s3 ls s3://cmip6-pds/CMIP6/CMIP/NOAA-GFDL/GFDL-CM4/ --no-sign-request`

### Memory errors
- Reduce spatial range (lat/lon)
- Reduce temporal range (dates)
- Use `get_zarr_summary_statistics()` instead of full data queries

### Import errors
- Run `uv sync` or `pip install -e .` in the MCP directory
- Check that zarr is installed: `python -c "import zarr; print(zarr.__version__)"`
