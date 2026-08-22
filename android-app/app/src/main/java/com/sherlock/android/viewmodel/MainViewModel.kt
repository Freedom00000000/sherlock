package com.sherlock.android.viewmodel

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.viewModelScope
import com.sherlock.android.model.CheckResult
import com.sherlock.android.model.ResultStatus
import com.sherlock.android.service.DataLoader
import com.sherlock.android.service.SiteChecker
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

private val CHEATER_SITES = setOf(
    "DanishDatingNet", "DenmarkPassions", "Nydate", "datingRU",
    "APClips", "AdmireMe.Vip", "BongaCams", "ChaturBate", "Erome",
    "Image Fap", "LushStories", "Motherless", "PocketStars", "Pornhub",
    "RedTube", "RocketTube", "TnAFlix", "Xvideos", "YouPorn", "xHamster",
    "Instagram", "Snapchat", "TikTok", "Twitter", "Telegram",
    "Reddit", "Discord", "Kik", "Flickr"
)

class MainViewModel(application: Application) : AndroidViewModel(application) {

    private val dataLoader = DataLoader(application)
    private val checker = SiteChecker()

    private val _result = MutableLiveData<CheckResult>()
    val result: LiveData<CheckResult> = _result

    private val _progress = MutableLiveData<Pair<Int, Int>>()
    val progress: LiveData<Pair<Int, Int>> = _progress

    private val _isRunning = MutableLiveData(false)
    val isRunning: LiveData<Boolean> = _isRunning

    private val _foundCount = MutableLiveData(0)
    val foundCount: LiveData<Int> = _foundCount

    private var searchJob: Job? = null

    fun search(username: String, cheaterMode: Boolean = false) {
        if (_isRunning.value == true) return

        _isRunning.value = true
        _foundCount.value = 0

        searchJob = viewModelScope.launch {
            val allSites = withContext(Dispatchers.IO) { dataLoader.loadSites() }
            val sites = if (cheaterMode) allSites.filter { it.name in CHEATER_SITES } else allSites
            val total = sites.size
            var found = 0

            sites.forEachIndexed { index, site ->
                if (!isActive) return@launch
                val checkResult = withContext(Dispatchers.IO) {
                    checker.check(site, username)
                }
                _result.value = checkResult
                if (checkResult.status == ResultStatus.FOUND) {
                    found++
                    _foundCount.value = found
                }
                _progress.value = Pair(index + 1, total)
            }

            _isRunning.value = false
        }
    }

    fun stop() {
        searchJob?.cancel()
        _isRunning.value = false
    }
}
