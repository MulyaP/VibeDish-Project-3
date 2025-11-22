# Supabase Migration Complete

## Summary
All routers have been migrated from SQLAlchemy to Supabase Python client.

## Changes Made

### 1. Database Connection (`app/db.py`)
- Removed SQLAlchemy engine and session management
- Added Supabase client initialization
- `get_db()` now returns the Supabase client directly

### 2. Configuration (`app/config.py`)
- Added `SUPABASE_KEY` field
- Auto-derives from `SUPABASE_SERVICE_ROLE_KEY` or `SUPABASE_ANON_KEY`

### 3. Routers Converted

#### `catalog.py`
- `list_restaurants()` - Uses `.select()`, `.ilike()`, `.order()`, `.range()`
- `list_meals_for_restaurant()` - Uses `.eq()`, `.gt()` for filtering

#### `meals.py`
- `list_meals()` - Uses `.select()`, `.gt()`, `.order()`, `.limit()`

#### `me.py`
- `get_me()` - Uses `.select().eq()`
- `patch_me()` - Uses `.update().eq()`

#### `address.py`
- All CRUD operations converted to Supabase table operations
- Uses `.insert()`, `.update()`, `.delete()`, `.select()`

#### `cart.py`
- Complete rewrite using Supabase client
- Removed async/await (now synchronous)
- Uses table operations with joins via `select("*, meals(*)")`

#### `orders.py`
- Complete rewrite using Supabase client
- All order lifecycle operations converted
- Status transitions and timeline tracking

## Installation

```bash
pip install supabase
```

## Environment Variables Required

Add to your `.env` file:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key-or-anon-key
# OR
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key
```

## Benefits

1. **No more pgbouncer issues** - Supabase handles connection pooling
2. **Simpler code** - No async/await complexity
3. **Better performance** - Direct REST API calls
4. **Easier to maintain** - Cleaner, more readable code
5. **Built-in features** - Row-level security, realtime subscriptions available

## Testing

Restart your FastAPI server:

```bash
uvicorn app.main:app --reload
```

All endpoints should work without the prepared statement errors.

## Notes

- All functions are now synchronous (removed `async`/`await`)
- Supabase client handles retries and connection management
- Foreign key relationships accessed via nested selects: `select("*, meals(*)")`
- Transactions are handled at the database level via RLS policies
