package com.sherlock.android

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.inputmethod.EditorInfo
import android.view.inputmethod.InputMethodManager
import androidx.activity.viewModels
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import com.sherlock.android.adapter.ResultsAdapter
import com.sherlock.android.databinding.ActivityMainBinding
import com.sherlock.android.viewmodel.MainViewModel

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private val viewModel: MainViewModel by viewModels()
    private val adapter = ResultsAdapter()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupRecyclerView()
        setupButtons()
        setupSwitches()
        observeViewModel()
    }

    private fun setupRecyclerView() {
        binding.rvResults.layoutManager = LinearLayoutManager(this)
        binding.rvResults.adapter = adapter
    }

    private fun setupButtons() {
        binding.btnSearch.setOnClickListener { startSearch() }
        binding.btnStop.setOnClickListener { viewModel.stop() }
        binding.etUsername.setOnEditorActionListener { _, actionId, _ ->
            if (actionId == EditorInfo.IME_ACTION_SEARCH) {
                startSearch(); true
            } else false
        }
        binding.btnSpiderFoot.setOnClickListener { runSpiderFoot() }
    }

    private fun setupSwitches() {
        binding.switchFoundOnly.setOnCheckedChangeListener { _, checked ->
            adapter.setFoundOnly(checked)
        }
    }

    private fun startSearch() {
        val username = binding.etUsername.text.toString().trim()
        if (username.isEmpty()) {
            binding.tilUsername.error = getString(R.string.error_empty_username)
            return
        }
        binding.tilUsername.error = null
        hideKeyboard()
        adapter.clear()
        binding.tvFoundCount.text = getString(R.string.found_count, 0)
        val cheaterMode = binding.chipModeCheater.isChecked
        viewModel.search(username, cheaterMode)
    }

    private fun observeViewModel() {
        viewModel.result.observe(this) { result ->
            adapter.addResult(result)
        }

        viewModel.progress.observe(this) { (current, total) ->
            binding.progressBar.max = total
            binding.progressBar.progress = current
            binding.tvProgress.text = getString(R.string.progress_format, current, total)
        }

        viewModel.isRunning.observe(this) { running ->
            binding.btnSearch.isEnabled = !running
            binding.btnStop.isEnabled = running
            binding.progressBar.visibility = if (running) android.view.View.VISIBLE else android.view.View.GONE
            binding.tvProgress.visibility = if (running) android.view.View.VISIBLE else android.view.View.GONE
        }

        viewModel.foundCount.observe(this) { count ->
            binding.tvFoundCount.text = getString(R.string.found_count, count)
        }

        viewModel.osintRunning.observe(this) { running ->
            binding.btnSpiderFoot.isEnabled = !running
            binding.btnSpiderFoot.text = if (running)
                "SpiderFoot scanning…"
            else
                getString(R.string.btn_spiderfoot)
        }

        viewModel.osintResults.observe(this) { results ->
            val sb = StringBuilder()
            for (r in results) {
                val status = if (r.found) "✓ FOUND" else "✗ NOT FOUND"
                sb.appendLine("${r.platform}  —  $status")
                for (d in r.details) sb.appendLine("   $d")
                if (r.found && r.url != null) sb.appendLine("   ${r.url}")
                sb.appendLine()
            }
            AlertDialog.Builder(this)
                .setTitle(getString(R.string.osint_title))
                .setMessage(sb.toString().trimEnd())
                .setPositiveButton("Close", null)
                .setNeutralButton("Open GitHub") { _, _ ->
                    val username = binding.etUsername.text.toString().trim()
                    if (username.isNotEmpty()) {
                        startActivity(Intent(Intent.ACTION_VIEW,
                            Uri.parse("https://github.com/$username")))
                    }
                }
                .show()
        }
    }

    private fun runSpiderFoot() {
        val username = binding.etUsername.text.toString().trim()
        if (username.isEmpty()) {
            binding.tilUsername.error = getString(R.string.error_empty_username)
            return
        }
        binding.tilUsername.error = null
        hideKeyboard()
        viewModel.runSpiderFoot(username)
    }

    private fun hideKeyboard() {
        val imm = getSystemService(InputMethodManager::class.java)
        imm.hideSoftInputFromWindow(binding.etUsername.windowToken, 0)
    }
}
