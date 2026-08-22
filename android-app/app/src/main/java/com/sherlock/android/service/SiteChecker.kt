package com.sherlock.android.service

import com.sherlock.android.model.CheckResult
import com.sherlock.android.model.ResultStatus
import com.sherlock.android.model.SiteInfo
import okhttp3.OkHttpClient
import okhttp3.Request
import java.util.concurrent.TimeUnit

class SiteChecker {

    private val client = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(15, TimeUnit.SECONDS)
        .followRedirects(false)
        .build()

    private val clientFollowRedirects = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(15, TimeUnit.SECONDS)
        .followRedirects(true)
        .build()

    fun check(site: SiteInfo, username: String): CheckResult {
        if (site.regexCheck != null) {
            val regex = Regex(site.regexCheck)
            if (!regex.containsMatchIn(username)) {
                return CheckResult(
                    siteName = site.name,
                    url = site.url.replace("{}", username),
                    status = ResultStatus.NOT_FOUND,
                    errorMessage = "Username format not valid for this site",
                    isDanishDating = site.isDanishDating
                )
            }
        }

        val targetUrl = site.url.replace("{}", username)

        return try {
            when (site.errorType) {
                "status_code" -> checkStatusCode(site, targetUrl)
                "message" -> checkMessage(site, targetUrl)
                "response_url" -> checkResponseUrl(site, targetUrl)
                else -> CheckResult(site.name, targetUrl, ResultStatus.ERROR, "Unknown errorType", site.isDanishDating)
            }
        } catch (e: Exception) {
            CheckResult(site.name, targetUrl, ResultStatus.ERROR, e.message, site.isDanishDating)
        }
    }

    private fun checkStatusCode(site: SiteInfo, url: String): CheckResult {
        val request = Request.Builder().url(url).get().build()
        client.newCall(request).execute().use { response ->
            val found = response.isSuccessful
            return CheckResult(
                siteName = site.name,
                url = url,
                status = if (found) ResultStatus.FOUND else ResultStatus.NOT_FOUND,
                isDanishDating = site.isDanishDating
            )
        }
    }

    private fun checkMessage(site: SiteInfo, url: String): CheckResult {
        if (site.errorMsgs.isEmpty()) {
            return CheckResult(site.name, url, ResultStatus.ERROR, "No errorMsg defined", site.isDanishDating)
        }
        val request = Request.Builder().url(url).get().build()
        clientFollowRedirects.newCall(request).execute().use { response ->
            val body = response.body?.string() ?: ""
            val notFound = site.errorMsgs.any { msg -> body.contains(msg) }
            return CheckResult(
                siteName = site.name,
                url = url,
                status = if (notFound) ResultStatus.NOT_FOUND else ResultStatus.FOUND,
                isDanishDating = site.isDanishDating
            )
        }
    }

    // response_url sites return HTTP 200 for existing users but redirect (3xx)
    // to an error/login page when the user doesn't exist.
    private fun checkResponseUrl(site: SiteInfo, url: String): CheckResult {
        val request = Request.Builder().url(url).get().build()
        client.newCall(request).execute().use { response ->
            val found = response.isSuccessful
            return CheckResult(
                siteName = site.name,
                url = url,
                status = if (found) ResultStatus.FOUND else ResultStatus.NOT_FOUND,
                isDanishDating = site.isDanishDating
            )
        }
    }
}
