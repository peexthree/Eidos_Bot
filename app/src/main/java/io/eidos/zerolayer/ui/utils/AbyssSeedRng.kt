package io.eidos.zerolayer.ui.utils

import java.security.MessageDigest
import kotlin.random.Random

/**
 * 🎲 6. CRYPTOGRAPHIC SEED GENERATION ENGINE FOR ABYSS RUNS
 * Generates deterministic Abyss layouts, enemy encounters, and anomaly drops based on SHA-256 Seed Strings.
 * Enables speedrunning, seed sharing, and reproducible raid runs.
 */
class AbyssSeedRng(val seedString: String) {

    private val seedHash: Long = hashSeedToLong(seedString)
    private val random = Random(seedHash)

    fun nextInt(from: Int, until: Int): Int {
        return random.nextInt(from, until)
    }

    fun nextFloat(): Float {
        return random.nextFloat()
    }

    fun nextBoolean(): Boolean {
        return random.nextBoolean()
    }

    fun <T> randomChoice(list: List<T>): T {
        return list[random.nextInt(0, list.size)]
    }

    companion object {
        fun generateRandomSeed(): String {
            val chars = "0123456789ABCDEF"
            val part1 = (1..4).map { chars.random() }.joinToString("")
            val part2 = (1..4).map { chars.random() }.joinToString("")
            return "EIDOS-$part1-$part2"
        }

        private fun hashSeedToLong(seed: String): Long {
            return try {
                val bytes = MessageDigest.getInstance("SHA-256").digest(seed.toByteArray())
                var hash = 0L
                for (i in 0..7) {
                    hash = (hash shl 8) or (bytes[i].toLong() and 0xFF)
                }
                hash
            } catch (e: Exception) {
                seed.hashCode().toLong()
            }
        }
    }
}
