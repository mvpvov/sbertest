import asyncio
import glob
import os
import random
import string

import pandas as pd
from crowd_sdk.tagme import TagmeClientAdvanced
from crowd_sdk.tagme.types import TaskDataRequest, TaskType

#Загрузка конфига crowd.cfg
async def main() -> None:
    config_candidates = glob.glob("*cfg") + glob.glob(".*cfg")
    if not config_candidates:
        raise FileNotFoundError("Не найден файл конфига (*cfg) в текущей папке")
    config_path = config_candidates[0]
    print(f"Конфиг: {config_path!r}")

    client = TagmeClientAdvanced(config_path)

#Создание тестового проекта
    try:
        random_name = "".join(random.choices(string.ascii_letters + string.digits, k=10))
        project = await client.create_project(
            name=random_name,
            description="Тестовый проект",
        )
        print(f"Создан проект: uid={project.uid}, name={random_name}")

#Создание task1,task2,task3
        tasks = {}
        for i in range(1, 4):
            req = TaskDataRequest(
                project_id=project.uid,
                organization_id=project.organization_id,
                name=str(i),
                overlap=1,
                type=TaskType.PROD,
                description=f"Задача {i}",
            )
            tasks[i] = await client.create_task(req)
            print(f"Создана таска {i}: uid={tasks[i].uid}")

        task1, task2, task3 = tasks[1], tasks[2], tasks[3]

#Обновление overlap Task1
        task1.overlap = 82
        task1 = await client.update_task(task=task1)
        print(f"Task 1 overlap обновлён: {task1.overlap}")

#Обновление priority Task2
        task2.priority = 82
        task2 = await client.update_task(task=task2)
        print(f"Task 2 priority обновлён: {task2.priority}")

#Создание random.txt
        os.makedirs("random_txt", exist_ok=True)
        txt_paths = []
        for i in range(3):
            text = "".join(random.choices(string.ascii_letters + " ", k=200))
            path = os.path.join("random_txt", f"doc_{i}.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            txt_paths.append(path)

        await client.upload_files(task_id=task3.uid, filepaths=txt_paths)
        print(f"Загружено файлов в task 3: {len(txt_paths)}")

        found_projects = await client.get_projects_by_name(project_name="Тестовый проект")
        if not found_projects:
            raise RuntimeError('Проект не найден')
        test_project = found_projects[0]

#Проверка Task в тестовом проекте
        project_tasks = await client.get_project_tasks(project_id=test_project.uid)
        target_task = next((t for t in project_tasks if t.name == "task"), None)
        if target_task is None:
            raise RuntimeError('Таска не найдена в "Тестовый проект"')

        results_df = await client.get_task_assignments_df(target_task.uid)

        task_files = await client.get_task_files(task_id=target_task.uid)
        print("Пример объекта TaskFile:", vars(task_files[0]) if task_files else "файлов нет")

        file_rows = []
        for tf in task_files:
            file_id = getattr(tf, "uid", None) or getattr(tf, "file_id", None) or getattr(tf, "id", None)
            content_bytes = await client.download_file(task_id=target_task.uid, file_id=file_id)
            try:
                text = content_bytes.decode("utf-8")
            except UnicodeDecodeError:
                text = content_bytes.decode("utf-8", errors="replace")
            file_rows.append({"file_name": tf.name, "INPUT:text": text})

        files_text_df = pd.DataFrame(file_rows)

        print("Колонки results_df:", results_df.columns.tolist())
        print("Колонки files_text_df:", files_text_df.columns.tolist())

        results_df = results_df.merge(files_text_df, on="file_name", how="left")

        output_path = "task_results.xlsx"
        results_df.to_excel(output_path, index=False)
        print(f"Результаты сохранены в {output_path}")

        start_stop_task = next((t for t in project_tasks if t.name == "start/stop task"), None)
        if start_stop_task is None:
            raise RuntimeError('Таска "start/stop task" не найдена в "Тестовый проект"')

        await client.start_task(start_stop_task.uid)
        print("Task started")

        await client.stop_task(start_stop_task.uid)
        print("Task stopped")

    finally:
        close_result = client.close()
        if asyncio.iscoroutine(close_result):
            await close_result


if __name__ == "__main__":
    asyncio.run(main())
