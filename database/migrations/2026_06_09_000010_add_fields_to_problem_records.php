<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('problem_records', function (Blueprint $table) {
            $table->string('model')->nullable()->after('report_id');
            $table->string('op_st')->nullable()->after('model');
            $table->string('factor')->nullable()->after('corrective_action');
        });
    }

    public function down(): void
    {
        Schema::table('problem_records', function (Blueprint $table) {
            $table->dropColumn(['model', 'op_st', 'factor']);
        });
    }
};
