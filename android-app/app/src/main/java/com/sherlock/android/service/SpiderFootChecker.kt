package com.sherlock.android.service

import com.google.gson.JsonParser
import com.sherlock.android.model.OsintResult
import okhttp3.OkHttpClient
import okhttp3.Request
import java.security.MessageDigest
import java.util.concurrent.TimeUnit

class SpiderFootChecker {

    private val client = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(10, TimeUnit.SECONDS)
        .followRedirects(true)
        .build()

    fun checkAll(username: String): List<OsintResult> = listOf(
        checkGitHub(username),
        checkKeybase(username),
        checkGravatar(username)
    )

    private fun checkGitHub(username: String): OsintResult {
        return try {
            val req = Request.Builder()
                .url("https://api.github.com/users/$username")
                .header("Accept", "application/vnd.github.v3+json")
                .build()
            client.newCall(req).execute().use { resp ->
                if (!resp.isSuccessful) {
                    OsintResult("GitHub", false, "https://github.com/$username")
                } else {
                    val json = JsonParser.parseString(resp.body?.string() ?: "{}").asJsonObject
                    val details = mutableListOf<String>()
                    json.get("name")?.asString?.let { details.add("Name: $it") }
                    json.get("bio")?.asString?.let { if (it.isNotBlank()) details.add("Bio: $it") }
                    json.get("location")?.asString?.let { if (it.isNotBlank()) details.add("Location: $it") }
                    json.get("public_repos")?.asInt?.let { details.add("Public repos: $it") }
                    json.get("followers")?.asInt?.let { details.add("Followers: $it") }
                    OsintResult("GitHub", true, "https://github.com/$username", details)
                }
            }
        } catch (e: Exception) {
            OsintResult("GitHub", false, null, listOf("Error: ${e.message}"))
        }
    }

    private fun checkKeybase(username: String): OsintResult {
        return try {
            val req = Request.Builder()
                .url("https://keybase.io/_/api/1.0/user/lookup.json?username=$username")
                .build()
            client.newCall(req).execute().use { resp ->
                val json = JsonParser.parseString(resp.body?.string() ?: "{}").asJsonObject
                val code = json.getAsJsonObject("status")?.get("code")?.asInt ?: -1
                if (code != 0) {
                    OsintResult("Keybase", false, "https://keybase.io/$username")
                } else {
                    val them = json.getAsJsonArray("them")?.firstOrNull()?.asJsonObject
                    val profile = them?.getAsJsonObject("profile")
                    val details = mutableListOf<String>()
                    profile?.get("full_name")?.asString?.let { if (it.isNotBlank()) details.add("Name: $it") }
                    profile?.get("location")?.asString?.let { if (it.isNotBlank()) details.add("Location: $it") }
                    profile?.get("bio")?.asString?.let { if (it.isNotBlank()) details.add("Bio: $it") }
                    OsintResult("Keybase", true, "https://keybase.io/$username", details)
                }
            }
        } catch (e: Exception) {
            OsintResult("Keybase", false, null, listOf("Error: ${e.message}"))
        }
    }

    private fun checkGravatar(username: String): OsintResult {
        return try {
            val hash = md5(username.lowercase())
            val req = Request.Builder()
                .url("https://www.gravatar.com/avatar/$hash?d=404&s=1")
                .build()
            client.newCall(req).execute().use { resp ->
                OsintResult(
                    "Gravatar",
                    resp.isSuccessful,
                    if (resp.isSuccessful) "https://www.gravatar.com/$hash" else null
                )
            }
        } catch (e: Exception) {
            OsintResult("Gravatar", false, null)
        }
    }

    private fun md5(input: String): String {
        val bytes = MessageDigest.getInstance("MD5").digest(input.toByteArray())
        return bytes.joinToString("") { "%02x".format(it) }
    }
}
