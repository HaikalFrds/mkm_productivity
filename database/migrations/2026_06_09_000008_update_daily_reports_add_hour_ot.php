<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('daily_reports', function (Blueprint $table) {
            $table->float('hour')->default(8)->after('shift');
            $table->float('ot')->default(0)->after('hour');
            $table->boolean('hari_pengganti')->default(false)->after('ot');
        });
    }

    public function down(): void
    {
        Schema::table('daily_reports', function (Blueprint $table) {
            $table->dropColumn(['hour', 'ot', 'hari_pengganti']);
        });
    }
};
