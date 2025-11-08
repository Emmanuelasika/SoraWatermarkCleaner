# Retry Logic and Timeout Configuration Summary

## ✅ Changes Implemented

### 1. **Retry Logic** 
- **Maximum retries**: 3 attempts (4 total attempts including initial)
- **Exponential backoff**: 2^retry_count seconds (2s, 4s, 8s, max 60s)
- **Smart error classification**: 
  - **Retryable errors**: Broken pipe, timeout, connection issues, FFmpeg crashes
  - **Non-retryable errors**: File not found, invalid format, model initialization failures
- **Automatic retry**: Tasks automatically retry on transient failures
- **Progress tracking**: Retry count stored in database and visible in API responses

### 2. **FFmpeg Optimization**
- **Changed preset**: From "slow" to "medium" for faster encoding
- **Better error handling**: Captures FFmpeg stderr for detailed error messages
- **Process monitoring**: Checks if FFmpeg process is alive before writing frames
- **Graceful cleanup**: Properly terminates FFmpeg process on errors

### 3. **Error Reporting**
- **Error messages**: Stored in database and returned in API responses
- **Retry count**: Tracked and visible in API responses
- **Detailed logging**: Full tracebacks logged for debugging

## ⏱️ Timeout Analysis

### Current Setting: 1200 seconds (20 minutes)

**Is it enough?** ⚠️ **Barely, might be tight for longer videos**

### Processing Time Estimates

For your video (18.36 MB, ~4200 frames, ~2.3 minutes):

| Phase | Progress | Estimated Time |
|-------|----------|----------------|
| Detection | 10-50% | 3-7 minutes |
| Removal | 50-95% | 10-30 minutes |
| Audio Merge | 95-99% | 10-30 seconds |
| **Total** | | **15-40 minutes** |

**1200 seconds (20 min)**: ⚠️ May timeout on videos with many watermarks

### Recommended Timeout: 3600 seconds (60 minutes)

**Why 60 minutes?**
- ✅ Handles most videos reliably
- ✅ Accounts for retries (3 retries × 20 min = 60 min worst case)
- ✅ Provides buffer for slower processing
- ✅ Better user experience (less timeout errors)

### Timeout by Video Length

| Video Length | Estimated Processing | Recommended Timeout |
|--------------|---------------------|---------------------|
| < 1 minute | 5-15 minutes | 1200s (20 min) ✅ |
| 1-2 minutes | 15-30 minutes | 2400s (40 min) ⚠️ |
| 2-5 minutes | 30-60 minutes | 3600s (60 min) ✅ |
| > 5 minutes | 60+ minutes | 7200s (120 min) ⚠️ |

## 🎯 Recommendations

### 1. **Set Timeout to 3600 seconds (60 minutes)**
   - Safe for most videos
   - Accounts for retries
   - Better reliability

### 2. **Monitor Processing Times**
   - Track actual processing times
   - Adjust timeout based on real data
   - Consider video length limits if needed

### 3. **Retry Logic Benefits**
   - Automatically handles transient failures
   - Reduces manual intervention
   - Improves success rate

## 📊 Expected Behavior

### Success Scenario
1. Task submitted
2. Processing starts (10% progress)
3. Detection phase (10-50%)
4. Removal phase (50-95%)
5. Audio merge (95-99%)
6. Task completes (100%)

### Retry Scenario
1. Task submitted
2. Processing starts
3. Error occurs (e.g., FFmpeg broken pipe)
4. **Automatic retry after 2 seconds** (attempt 2/4)
5. If fails again, **retry after 4 seconds** (attempt 3/4)
6. If fails again, **retry after 8 seconds** (attempt 4/4)
7. If all retries fail, task marked as ERROR

### Error Types

**Retryable (will retry automatically):**
- Broken pipe errors
- FFmpeg crashes
- Timeout errors
- Connection issues
- Temporary failures

**Non-retryable (fails immediately):**
- File not found
- Invalid video format
- Model initialization failures
- Corrupted video files

## 🚀 Next Steps

1. **Update RunPod timeout to 3600 seconds (60 minutes)**
2. **Deploy the updated code**
3. **Test with your video again**
4. **Monitor logs for retry behavior**
5. **Adjust timeout if needed based on real data**

## 📝 Code Changes Summary

### Files Modified:
1. `sorawm/server/models.py` - Added `retry_count` field
2. `sorawm/server/worker.py` - Added retry logic with exponential backoff
3. `sorawm/core.py` - Changed FFmpeg preset to "medium", improved error handling
4. `sorawm/server/schemas.py` - Added `retry_count` to response schema
5. `test_video_upload.py` - Updated to show error messages and retry counts

### Database Changes:
- New column: `retry_count` (integer, default 0)
- Existing column: `error_message` (already added)

**Note**: Database migration will happen automatically on first run (SQLAlchemy creates tables if they don't exist).

