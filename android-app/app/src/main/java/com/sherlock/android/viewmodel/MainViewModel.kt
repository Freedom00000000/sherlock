package com.sherlock.android.viewmodel

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.viewModelScope
import com.sherlock.android.model.CheckResult
import com.sherlock.android.model.OsintResult
import com.sherlock.android.model.ResultStatus
import com.sherlock.android.service.DataLoader
import com.sherlock.android.service.SiteChecker
import com.sherlock.android.service.SpiderFootChecker
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.async
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.sync.Semaphore
import kotlinx.coroutines.sync.withPermit

private val CHEATER_SITES = setOf(
    "DanishDatingNet", "DenmarkPassions", "Nydate", "datingRU",
    "APClips", "AdmireMe.Vip", "BongaCams", "ChaturBate", "Erome",
    "Image Fap", "LushStories", "Motherless", "PocketStars", "Pornhub",
    "RedTube", "RocketTube", "TnAFlix", "Xvideos", "YouPorn", "xHamster",
    "Instagram", "Snapchat", "TikTok", "Twitter", "Telegram",
    "Reddit", "Discord", "Kik", "Flickr"
)

private const val MAX_CONCURRENT = 15

class MainViewModel(application: Application) : AndroidViewModel(application) {

    private val dataLoader = DataLoader(application)
    private val checker = SiteChecker()
    private val spiderFootChecker = SpiderFootChecker()

    private val _result = MutableLiveData<CheckResult>()
    val result: LiveData<CheckResult> = _result

    private val _progress = MutableLiveData<Pair<Int, Int>>()
    val progress: LiveData<Pair<Int, Int>> = _progress

    private val _isRunning = MutableLiveData(false)
    val isRunning: LiveData<Boolean> = _isRunning

    private val _foundCount = MutableLiveData(0)
    val foundCount: LiveData<Int> = _foundCount

    private val _osintResults = MutableLiveData<List<OsintResult>>()
    val osintResults: LiveData<List<OsintResult>> = _osintResults

    private val _osintRunning = MutableLiveData(false)
    val osintRunning: LiveData<Boolean> = _osintRunning

    private var searchJob: Job? = null

    fun search(username: String, cheaterMode: Boolean = false) {
        if (_isRunning.value == true) return

        _isRunning.value = true
        _foundCount.value = 0

        searchJob = viewModelScope.launch {
            try {
                val allSites = kotlinx.coroutines.withContext(Dispatchers.IO) {
                    dataLoader.loadSites()
                }
                val sites = if (cheaterMode) allSites.filter { it.name in CHEATER_SITES } else allSites
                val total = sites.size
                val semaphore = Semaphore(MAX_CONCURRENT)
                var found = 0
                var done = 0

                val deferreds = sites.map { site ->
                    async(Dispatchers.IO) {
                        semaphore.withPermit { checker.check(site, username) }
                    }
                }

                for (deferred in deferreds) {
                    if (!isActive) break
                    val checkResult = deferred.await()
                    _result.value = checkResult
                    done++
                    if (checkResult.status == ResultStatus.FOUND) {
                        found++
                        _foundCount.value = found
                    }
                    _progress.value = Pair(done, total)
                }
            } finally {
                _isRunning.value = false
            }
        }
    }

    fun stop() {
        searchJob?.cancel()
        _isRunning.value = false
    }

    fun runSpiderFoot(username: String) {
        if (_osintRunning.value == true) return
        _osintRunning.value = true
        viewModelScope.launch {
            try {
                val results = kotlinx.coroutines.withContext(Dispatchers.IO) {
                    spiderFootChecker.checkAll(username)
                }
                _osintResults.value = results
            } finally {
                _osintRunning.value = false
            }
        }
    }
}
