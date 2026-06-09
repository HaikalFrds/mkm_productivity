<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('problem_records', function (Blueprint $table) {
            $table->id();
            $table->foreignId('report_id')->constrained('daily_reports')->cascadeOnDelete();
            $table->string('category')->nullable();
            $table->string('ra_number')->nullable();
            $table->text('description')->nullable();
            $table->text('cause')->nullable();
            $table->text('corrective_action')->nullable();
            $table->string('pic')->nullable();
            $table->time('start_time')->nullable();
            $table->time('end_time')->nullable();
            $table->float('down_time')->default(0);
            $table->float('loss_time')->default(0);
            $table->date('date')->nullable();
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('problem_records');
    }
};
