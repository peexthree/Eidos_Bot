plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.kotlin.serialization)
    alias(libs.plugins.ksp)
}

android {
    namespace = "io.eidos.zerolayer"
    compileSdk = 35

    defaultConfig {
        applicationId = "io.eidos.zerolayer"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"

        fun resolveEnv(vararg primaryKeys: String): String {
            for (key in primaryKeys) {
                val value = System.getenv(key)
                if (!value.isNullOrBlank()) {
                    return value.trim().removeSurrounding("\"").removeSurrounding("'")
                }
            }
            return ""
        }

        val supabaseUrl = resolveEnv("SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL", "PUBLIC_SUPABASE_URL")
        val supabaseAnonKey = resolveEnv("SUPABASE_ANON_KEY", "NEXT_PUBLIC_SUPABASE_ANON_KEY", "SUPABASE_KEY")
        val geminiKey = (System.getenv("GEMINI_API_KEY") ?: "").trim().removeSurrounding("\"").removeSurrounding("'")

        buildConfigField("String", "GEMINI_API_KEY", "\"$geminiKey\"")
        buildConfigField("String", "SUPABASE_URL", "\"$supabaseUrl\"")
        buildConfigField("String", "SUPABASE_ANON_KEY", "\"$supabaseAnonKey\"")
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_21
        targetCompatibility = JavaVersion.VERSION_21
    }
    kotlinOptions {
        jvmTarget = "21"
    }
    buildFeatures {
        compose = true
        buildConfig = true
    }
    bundle {
        language {
            enableSplit = false
        }
        density {
            enableSplit = true
        }
        abi {
            enableSplit = true
        }
    }
}

dependencies {
    // Material Components (for XML themes)
    implementation("com.google.android.material:material:1.12.0")

    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.activity.compose)
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.ui)
    implementation(libs.androidx.ui.graphics)
    implementation(libs.androidx.ui.tooling.preview)
    implementation(libs.androidx.material3)
    implementation(libs.androidx.navigation.compose)
    implementation(libs.androidx.media3.exoplayer)
    implementation(libs.androidx.media3.ui)
    implementation(libs.kotlinx.serialization.json)
    
    // Retrofit & OkHttp for Gemini REST API & Supabase
    implementation(libs.retrofit)
    implementation(libs.retrofit.converter.serialization)
    implementation(libs.okhttp)
    implementation(libs.okhttp.logging)
    
    // Supabase Postgrest
    implementation("io.github.jan-tennert.supabase:postgrest-kt:2.5.0")
    implementation("io.ktor:ktor-client-okhttp:2.3.12")
    
    // Room
    implementation(libs.androidx.room.runtime)
    implementation(libs.androidx.room.ktx)
    ksp(libs.androidx.room.compiler)
    
    // WorkManager
    implementation(libs.androidx.work.runtime.ktx)
    
    // Biometrics
    implementation("androidx.biometric:biometric:1.1.0")
    
    // Coil
    implementation(libs.coil.compose)
    implementation(libs.coil.svg)

    // Google Play Billing
    implementation("com.android.billingclient:billing-ktx:7.0.0")

    // Firebase BoM, Crashlytics & Analytics
    implementation(platform("com.google.firebase:firebase-bom:33.1.2"))
    implementation("com.google.firebase:firebase-crashlytics-ktx")
    implementation("com.google.firebase:firebase-analytics-ktx")

    testImplementation(libs.junit)
    androidTestImplementation(libs.androidx.junit)
    androidTestImplementation(libs.androidx.espresso.core)
    androidTestImplementation(platform(libs.androidx.compose.bom))
    androidTestImplementation(libs.androidx.ui.test.junit4)
    debugImplementation(libs.androidx.ui.tooling)
    debugImplementation(libs.androidx.ui.test.manifest)
}
