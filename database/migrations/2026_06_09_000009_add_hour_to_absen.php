<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('absen', function (Blueprint $table) {
            $table->float('hour')->default(0)->after('keterangan');
        });
    }

    public function down(): void
    {
        Schema::table('absen', function (Blueprint $table) {
            $table->dropColumn('hour');
        });
    }
};
