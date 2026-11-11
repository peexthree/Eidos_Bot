import java.util.Properties

plugins {
    alias(libs.plugins.android.application)
    // AGP 9 built-in Kotlin mode: org.jetbrains.kotlin.android must NOT be
    // applied (gradle.properties: android.builtInKotlin=true). Compose and
    // serialization compiler plugins still apply on top of built-in Kotlin.
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.kotlin.serialization)
    alias(libs.plugins.ksp)
}

val localProps = Properties().apply {
    val localPropertiesFile = rootProject.file("local.properties")
    if (localPropertiesFile.exists()) {
        localPropertiesFile.inputStream().use { stream ->
            load(stream)
        }
    }
}

// Release signing: keep real keystore out of git via keystore.properties
// (gitignored). See keystore.properties.example. Without the file, release
// builds fall back to the debug key so local builds still work.
val keystorePropsFile = rootProject.file("keystore.properties")
val keystoreProps = Properties().apply {
    if (keystorePropsFile.exists()) {
        keystorePropsFile.inputStream().use { stream ->
            load(stream)
        }
    }
}

fun resolveEnv(vararg primaryKeys: String): String {
    for (key in primaryKeys) {
        val fromLocalProps = localProps.getProperty(key)
        if (!fromLocalProps.isNullOrBlank()) {
            return fromLocalProps.trim().removeSurrounding("\"").removeSurrounding("'")
        }
        val fromProject = findProperty(key) as? String
        if (!fromProject.isNullOrBlank()) {
            return fromProject.trim().removeSurrounding("\"").removeSurrounding("'")
        }
        val fromEnv = System.getenv(key)
        if (!fromEnv.isNullOrBlank()) {
            return fromEnv.trim().removeSurrounding("\"").removeSurrounding("'")
        }
    }
    return ""
}

android {
    namespace = "io.eidos.zerolayer"
    // compileSdk 37 required by androidx 2026 line (core 1.19+, compose 1.12+,
    // navigation 2.10+). targetSdk intentionally stays 35 until Play requires it:
    // bumping targetSdk changes runtime behavior - do it as a separate step.
    compileSdk = 37

    defaultConfig {
        applicationId = "io.eidos.zerolayer"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"

        val supabaseUrl = resolveEnv("SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL", "PUBLIC_SUPABASE_URL")
        val supabaseAnonKey = resolveEnv("SUPABASE_ANON_KEY", "NEXT_PUBLIC_SUPABASE_ANON_KEY", "SUPABASE_KEY")
        buildConfigField("String", "SUPABASE_URL", "\"$supabaseUrl\"")
        buildConfigField("String", "SUPABASE_ANON_KEY", "\"$supabaseAnonKey\"")
    }
    signingConfigs {
        getByName("debug") {
            storeFile = file("debug.keystore")
            storePassword = "android"
            keyAlias = "androiddebugkey"
            keyPassword = "android"
        }
        create("release") {
            if (keystorePropsFile.exists()) {
                storeFile = rootProject.file(keystoreProps.getProperty("storeFile"))
                storePassword = keystoreProps.getProperty("storePassword")
                keyAlias = keystoreProps.getProperty("keyAlias")
                keyPassword = keystoreProps.getProperty("keyPassword")
            }
        }
    }

    buildTypes {
        debug {
            signingConfig = signingConfigs.getByName("debug")
            // Gemini key is a dev-only convenience: it ships in debug builds
            // for local experimentation. Release falls back to the built-in
            // local simulation (GeminiService) instead of leaking a billable
            // API key inside the APK. Long-term: proxy via a Supabase Edge
            // Function and restore real calls server-side.
            val geminiKey = resolveEnv("GEMINI_API_KEY")
            buildConfigField("String", "GEMINI_API_KEY", "\"$geminiKey\"")
        }
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
            buildConfigField("String", "GEMINI_API_KEY", "\"\"")
            signingConfig = if (keystorePropsFile.exists()) {
                signingConfigs.getByName("release")
            } else {
                logger.warn("keystore.properties not found: release build falls back to the DEBUG key (local use only!)")
                signingConfigs.getByName("debug")
            }
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    // AGP 9 built-in Kotlin DSL (replaces kotlinOptions)
    kotlin {
        compilerOptions {
            jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17)
        }
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
    testOptions {
        unitTests.all {
            it.jvmArgs("-Djava.net.preferIPv4Stack=true")
        }
    }
}

// Room: экспорт JSON-схем (app/schemas/...) - история версий для миграционных тестов
ksp {
    arg("room.schemaLocation", "$projectDir/schemas")
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
    // Icons left the Compose BOM in 2026 - explicit dependency now
    implementation(libs.androidx.material.icons.extended)
    implementation(libs.androidx.navigation.compose)
    implementation(libs.androidx.media3.exoplayer)
    implementation(libs.androidx.media3.ui)
    implementation(libs.kotlinx.serialization.json)
    
    // Retrofit & OkHttp for Gemini REST API & Supabase
    implementation(libs.retrofit)
    implementation(libs.retrofit.converter.serialization)
    implementation(libs.okhttp)
    implementation(libs.okhttp.logging)
    
    // Supabase Postgrest (compatible with Kotlin 2.2)
    implementation("io.github.jan-tennert.supabase:postgrest-kt:2.5.0")
    implementation("io.ktor:ktor-client-okhttp:2.3.12")

    // Room
    implementation(libs.androidx.room.runtime)
    implementation(libs.androidx.room.ktx)
    ksp(libs.androidx.room.compiler)

    // WorkManager
    implementation(libs.androidx.work.runtime.ktx)

    // Security & EncryptedSharedPreferences
    implementation(libs.androidx.security.crypto)

    // Biometrics
    implementation(libs.androidx.biometric)

    // Coil
    implementation(libs.coil.compose)
    implementation(libs.coil.svg)

    // Google Play Billing
    implementation(libs.billing.ktx)

    // Firebase BoM, Crashlytics & Analytics
    implementation(platform("com.google.firebase:firebase-bom:33.1.2"))
    implementation("com.google.firebase:firebase-crashlytics-ktx")
    implementation("com.google.firebase:firebase-analytics-ktx")

    // Миграционные тесты Room на JVM: реальный SQLite без эмулятора
    testImplementation("org.xerial:sqlite-jdbc:3.46.1.3")
    testImplementation(libs.junit)
    androidTestImplementation(libs.androidx.junit)
    androidTestImplementation(libs.androidx.espresso.core)
    androidTestImplementation(libs.androidx.test.rules)
    androidTestImplementation(libs.androidx.test.uiautomator)
    androidTestImplementation(platform(libs.androidx.compose.bom))
    androidTestImplementation(libs.androidx.ui.test.junit4)
    debugImplementation(libs.androidx.ui.tooling)
    debugImplementation(libs.androidx.ui.test.manifest)
}
