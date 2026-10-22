import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';

import '../catalog.dart';
import '../main.dart';
import '../state.dart';
import 'catalog.dart';

// Подбор материала под задачу: фундамент, подвал, бассейн, ремонт бетона
class TasksScreen extends StatelessWidget {
  const TasksScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final state = AppScope.of(context);
    final t = Theme.of(context).textTheme;
    return Scaffold(
      appBar: AppBar(title: const Text('Подбор материала')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text('Что нужно сделать?', style: t.titleLarge),
          const SizedBox(height: 12),
          for (final task in state.catalog.tasks)
            Card(
              clipBehavior: Clip.antiAlias,
              margin: const EdgeInsets.only(bottom: 12),
              child: InkWell(
                onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => TaskScreen(task: task))),
                child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                  AspectRatio(
                    aspectRatio: 16 / 7,
                    child: CachedNetworkImage(imageUrl: task.image, fit: BoxFit.cover, errorWidget: (_, _, _) => const SizedBox()),
                  ),
                  ListTile(
                    title: Text(task.title, style: t.titleMedium),
                    subtitle: Text(task.materials.map((m) => m.$1).take(3).join(', ')),
                    trailing: const Icon(Icons.chevron_right),
                  ),
                ]),
              ),
            ),
          Card(
            margin: EdgeInsets.zero,
            color: Theme.of(context).colorScheme.secondaryContainer,
            child: ListTile(
              leading: const Icon(Icons.photo_camera_outlined),
              title: const Text('Другая задача или не уверены?'),
              subtitle: const Text('Пришлите фото в WhatsApp — специалист подберёт систему материалов и посчитает количество.'),
              onTap: () => state.openWhatsApp('Здравствуйте! Помогите подобрать материал. Задача: '),
            ),
          ),
        ],
      ),
    );
  }
}

class TaskScreen extends StatelessWidget {
  const TaskScreen({super.key, required this.task});
  final Task task;

  @override
  Widget build(BuildContext context) {
    final state = AppScope.of(context);
    final t = Theme.of(context).textTheme;
    return Scaffold(
      appBar: AppBar(title: Text(task.title)),
      body: ListView(
        padding: const EdgeInsets.symmetric(vertical: 16),
        children: [
          Padding(padding: const EdgeInsets.symmetric(horizontal: 16), child: Text(task.lead, style: t.bodyLarge)),
          _heading(context, 'Материалы'),
          for (final (name, why) in task.materials)
            if (state.catalog.productByName(name) case final p?)
              ProductTile(product: p, subtitle: why)
            else
              ListTile(title: Text(name), subtitle: Text(why)),
          _heading(context, 'Как делать'),
          for (final (i, step) in task.steps.indexed)
            ListTile(leading: CircleAvatar(radius: 14, child: Text('${i + 1}')), title: Text(step)),
          _heading(context, 'Вопросы'),
          for (final (q, a) in task.faq)
            ExpansionTile(
              title: Text(q),
              childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
              children: [Text(a)],
            ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: FilledButton.icon(
              icon: const Icon(Icons.chat_outlined),
              label: const Text('Подобрать по фото в WhatsApp'),
              onPressed: () => state.openWhatsApp('Здравствуйте! ${task.title}: помогите подобрать материалы. '),
            ),
          ),
          Center(child: TextButton(onPressed: () => openUrl(task.url), child: const Text('Подробнее на kttron.kz'))),
        ],
      ),
    );
  }

  Widget _heading(BuildContext context, String text) => Padding(
        padding: const EdgeInsets.fromLTRB(16, 24, 16, 8),
        child: Text(text, style: Theme.of(context).textTheme.titleLarge),
      );
}
