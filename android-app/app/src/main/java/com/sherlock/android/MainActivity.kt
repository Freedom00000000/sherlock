package com.sherlock.android

import android.os.Bundle
import android.view.inputmethod.EditorInfo
import android.view.inputmethod.InputMethodManager
import androidx.activity.viewModels
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
        setupSearchButton()
        observeViewModel()
    }

    private fun setupRecyclerView() {
        binding.rvResults.layoutManager = LinearLayoutManager(this)
        binding.rvResults.adapter = adapter
    }

    private fun setupSearchButton() {
        binding.btnSearch.setOnClickListener { startSearch() }
        binding.etUsername.setOnEditorActionListener { _, actionId, _ ->
            if (actionId == EditorInfo.IME_ACTION_SEARCH) {
                startSearch()
                true
            } else false
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
        viewModel.search(username)
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
            binding.progressBar.visibility = if (running) android.view.View.VISIBLE else android.view.View.GONE
            binding.tvProgress.visibility = if (running) android.view.View.VISIBLE else android.view.View.GONE
        }

        viewModel.foundCount.observe(this) { count ->
            binding.tvFoundCount.text = getString(R.string.found_count, count)
        }
    }

    private fun hideKeyboard() {
        val imm = getSystemService(InputMethodManager::class.java)
        imm.hideSoftInputFromWindow(binding.etUsername.windowToken, 0)
    }
}
