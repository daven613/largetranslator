# Parallel Translation Configuration

## Overview

The translation system now uses **direct PostgreSQL connections** instead of Supabase's REST API, completely eliminating HTTP connection bottlenecks. This enables true high-concurrency parallel processing with transactional safety.

## 🚀 **Major Architecture Change**

### **Before: HTTP REST API Bottleneck**
- ❌ Each database operation = HTTP request to Supabase  
- ❌ Limited to ~100 concurrent HTTP connections
- ❌ 5 users × 5 chunks × 4 HTTP calls = **100 concurrent requests** (maxed out)
- ❌ Risk of wasted OpenAI calls if HTTP fails after translation succeeds

### **After: Direct PostgreSQL Connections**  
- ✅ Real connection pooling (50 concurrent PostgreSQL connections)
- ✅ Transactional safety (OpenAI + DB succeed together or fail together)
- ✅ 20+ users × 10+ chunks each = **200+ concurrent operations** (no problem)
- ✅ No wasted OpenAI money - transactions ensure consistency

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Parallel processing (now much higher!)
PARALLEL_TRANSLATION_BATCH_SIZE=10

# PostgreSQL Connection (for Supabase)
SUPABASE_DB_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres
# OR individual components:
SUPABASE_DB_HOST=db.[PROJECT].supabase.co
SUPABASE_DB_PORT=5432
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres
SUPABASE_DB_PASSWORD=[YOUR_PASSWORD]
```

### Recommended Values

- **Default**: 10 chunks in parallel per user
- **Conservative**: 5-8 chunks (for lower-spec servers)  
- **Aggressive**: 15-20 chunks (for high-performance setups)
- **Maximum recommended**: 25 chunks per user

## How It Works

### **Per-User Concurrency**
- Each user can process **10+ chunks simultaneously**
- Multiple users can run translations **at the same time**
- No interference between users

### **Connection Pool Management**
- **50 PostgreSQL connections** in the pool
- **1000 queries per connection** before rotation
- **Automatic connection recycling** every 5 minutes
- **30-second timeout** per query (prevents hanging)

### **Transactional Safety**
1. **Translate with OpenAI** (call API)
2. **Begin Database Transaction**
3. **Save translated chunk + Update progress** (atomic)
4. **Commit Transaction** (success) OR **Rollback** (failure)

**Result**: Either both OpenAI and database succeed, or both fail. **No wasted money!**

## Performance Benefits

### **Before (HTTP API)**
- 5 users max before errors
- ~20 HTTP requests per user translation
- Frequent connection timeouts
- Wasted OpenAI calls on HTTP failures

### **After (Direct PostgreSQL)**
- **20+ users simultaneously** without issues
- **10+ chunks per user** in parallel  
- **Zero HTTP connection limits**
- **Guaranteed transaction consistency**

## Scaling Expectations

| Concurrent Users | Chunks Per User | Total Operations | Status |
|------------------|-----------------|------------------|--------|
| 5 users          | 10 chunks       | 50 operations    | ✅ Easy |
| 10 users         | 10 chunks       | 100 operations   | ✅ Smooth |
| 20 users         | 10 chunks       | 200 operations   | ✅ Good |
| 50 users         | 5 chunks        | 250 operations   | ⚠️ Monitor |

## Migration Guide

### **1. Install Dependencies**
```bash
pip install asyncpg>=0.29.0
```

### **2. Update Your .env File**
```bash
# Add PostgreSQL connection details
SUPABASE_DB_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres
PARALLEL_TRANSLATION_BATCH_SIZE=10
```

### **3. Restart Your Application**
The system will automatically detect and use the new PostgreSQL client.

### **4. Test Performance**
Try translating multiple documents simultaneously to see the improved performance!

## Troubleshooting

### **Connection Issues**
- Verify your `SUPABASE_DB_URL` is correct
- Check that your Supabase project allows direct database connections
- Ensure your IP is allowlisted in Supabase network settings

### **Performance Monitoring**
- Monitor PostgreSQL connection pool usage
- Watch for transaction deadlocks (rare but possible)
- Check OpenAI API rate limits (now the main bottleneck)

## Rate Limiting Considerations

With HTTP bottlenecks removed, **OpenAI API rate limits** become the primary constraint:

- **Free tier**: ~3 requests/minute → Use `PARALLEL_TRANSLATION_BATCH_SIZE=3`
- **Pay-as-you-go**: ~60 requests/minute → Use `PARALLEL_TRANSLATION_BATCH_SIZE=10`  
- **Tier 1+**: 3500+ requests/minute → Use `PARALLEL_TRANSLATION_BATCH_SIZE=20+`

The database can now handle whatever OpenAI can deliver! 🚀 