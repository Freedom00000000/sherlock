package com.sherlock.android.adapter

import android.content.Intent
import android.net.Uri
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.cardview.widget.CardView
import androidx.recyclerview.widget.RecyclerView
import com.google.android.material.chip.Chip
import com.sherlock.android.R
import com.sherlock.android.model.CheckResult
import com.sherlock.android.model.ResultStatus

class ResultsAdapter : RecyclerView.Adapter<ResultsAdapter.ResultViewHolder>() {

    private val results = mutableListOf<CheckResult>()

    fun addResult(result: CheckResult) {
        results.add(0, result)
        notifyItemInserted(0)
    }

    fun clear() {
        results.clear()
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ResultViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_result, parent, false)
        return ResultViewHolder(view)
    }

    override fun onBindViewHolder(holder: ResultViewHolder, position: Int) {
        holder.bind(results[position])
    }

    override fun getItemCount() = results.size

    class ResultViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val card: CardView = itemView.findViewById(R.id.cardResult)
        private val tvSiteName: TextView = itemView.findViewById(R.id.tvSiteName)
        private val tvUrl: TextView = itemView.findViewById(R.id.tvUrl)
        private val chipStatus: Chip = itemView.findViewById(R.id.chipStatus)
        private val chipDanish: Chip = itemView.findViewById(R.id.chipDanish)

        fun bind(result: CheckResult) {
            tvSiteName.text = result.siteName
            tvUrl.text = result.url

            when (result.status) {
                ResultStatus.FOUND -> {
                    chipStatus.text = "FOUND"
                    chipStatus.setChipBackgroundColorResource(com.google.android.material.R.color.design_default_color_secondary)
                    card.setCardBackgroundColor(itemView.context.getColor(R.color.found_background))
                }
                ResultStatus.NOT_FOUND -> {
                    chipStatus.text = "NOT FOUND"
                    chipStatus.setChipBackgroundColorResource(com.google.android.material.R.color.material_on_surface_disabled)
                    card.setCardBackgroundColor(itemView.context.getColor(android.R.color.white))
                }
                ResultStatus.ERROR -> {
                    chipStatus.text = "ERROR"
                    chipStatus.setChipBackgroundColorResource(com.google.android.material.R.color.design_default_color_error)
                    card.setCardBackgroundColor(itemView.context.getColor(android.R.color.white))
                }
            }

            chipDanish.visibility = if (result.isDanishDating) View.VISIBLE else View.GONE

            if (result.status == ResultStatus.FOUND) {
                card.setOnClickListener {
                    val intent = Intent(Intent.ACTION_VIEW, Uri.parse(result.url))
                    itemView.context.startActivity(intent)
                }
            } else {
                card.setOnClickListener(null)
            }
        }
    }
}
